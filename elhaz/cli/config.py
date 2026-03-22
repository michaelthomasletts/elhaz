# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Config subcommands: add, list, get, update, remove."""

import os
import subprocess
from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Literal, Optional

import typer

from elhaz.config import Config
from elhaz.exceptions import (
    ElhazAlreadyExistsError,
    ElhazNotFoundError,
    ElhazValidationError,
)

from ..constants import state
from .output import print_error, print_json, print_success
from .prompts import (
    ask_text,
    ask_yes_no,
    list_local_configs,
    resolve_name,
    select_local_config,
)

app = typer.Typer(
    name="config",
    help="Manage elhaz configurations.",
    no_args_is_help=True,
)

FieldKind = Literal["scalar", "str_list", "model_list"]


@dataclass
class FieldDescriptor:
    """Descriptor for a single interactive config field.

    Parameters
    ----------
    key : str
        Dict key / Pydantic field name.
    label : str
        Human-readable prompt label.
    kind : FieldKind
        How to collect the value: ``scalar``, ``str_list``, or
        ``model_list``.
    cast : type
        Cast function applied to scalar input. Ignored for list kinds.
    hint : str or None
        Inline hint appended to the scalar prompt (e.g. ``"seconds"``).
    sub_fields : list[FieldDescriptor]
        Sub-field descriptors for ``model_list`` kinds.
    """

    key: str
    label: str
    kind: FieldKind = "scalar"
    cast: type = str
    hint: str | None = None
    sub_fields: list["FieldDescriptor"] = dc_field(default_factory=list)


_ASSUME_ROLE_OPTIONAL: list[FieldDescriptor] = [
    FieldDescriptor("RoleSessionName", "RoleSessionName"),
    FieldDescriptor(
        "DurationSeconds", "DurationSeconds", cast=int, hint="seconds"
    ),
    FieldDescriptor("ExternalId", "ExternalId"),
    FieldDescriptor("SerialNumber", "SerialNumber (MFA device ARN)"),
    FieldDescriptor("TokenCode", "TokenCode (MFA token)"),
    FieldDescriptor("SourceIdentity", "SourceIdentity"),
    FieldDescriptor("Policy", "Inline session policy (JSON string)"),
    FieldDescriptor(
        "PolicyArns", "PolicyArns", kind="str_list", hint="policy ARN"
    ),
    FieldDescriptor(
        "Tags",
        "Tags",
        kind="model_list",
        sub_fields=[
            FieldDescriptor("Key", "Key"),
            FieldDescriptor("Value", "Value"),
        ],
    ),
    FieldDescriptor(
        "TransitiveTagKeys",
        "TransitiveTagKeys",
        kind="str_list",
        hint="tag key",
    ),
    FieldDescriptor(
        "ProvidedContexts",
        "ProvidedContexts",
        kind="model_list",
        sub_fields=[
            FieldDescriptor("ProviderArn", "ProviderArn"),
            FieldDescriptor("ContextAssertion", "ContextAssertion"),
        ],
    ),
]

_STS_FIELDS: list[FieldDescriptor] = [
    FieldDescriptor("region_name", "Region name"),
    FieldDescriptor("api_version", "API version"),
    FieldDescriptor("use_ssl", "Use SSL?", cast=bool),
    FieldDescriptor("verify", "Verify SSL?", cast=bool),
    FieldDescriptor("endpoint_url", "STS endpoint URL"),
    FieldDescriptor("aws_access_key_id", "AWS access key ID"),
    FieldDescriptor("aws_secret_access_key", "AWS secret access key"),
    FieldDescriptor("aws_session_token", "AWS session token"),
    FieldDescriptor("aws_account_id", "AWS account ID"),
]

_SESSION_FIELDS: list[FieldDescriptor] = [
    FieldDescriptor("region_name", "Region name"),
    FieldDescriptor("profile_name", "AWS profile name"),
    FieldDescriptor("aws_account_id", "AWS account ID"),
    FieldDescriptor("aws_access_key_id", "AWS access key ID"),
    FieldDescriptor("aws_secret_access_key", "AWS secret access key"),
    FieldDescriptor("aws_session_token", "AWS session token"),
]


def _collect_str_list(
    descriptor: FieldDescriptor,
    existing: list[str] | None = None,
) -> list[str] | None:
    """Interactively collect a list of strings for *descriptor*.

    Parameters
    ----------
    descriptor : FieldDescriptor
        Field being collected.
    existing : list[str] or None, optional
        Current values shown when updating a config.

    Returns
    -------
    list[str] or None
        Collected items, or None if the user entered nothing.
    """

    if existing:
        typer.echo(f"  Current {descriptor.label}: {existing}")
        if not ask_yes_no(
            f"  Replace existing {descriptor.label}?", default=False
        ):
            return existing

    hint = f" ({descriptor.hint})" if descriptor.hint else ""
    typer.echo(f"  Enter {descriptor.label}{hint} — empty line to finish:")
    items: list[str] = []
    i = 1
    while True:
        val = ask_text(f"  [{i}]:", default="")
        if not val:
            break
        items.append(val)
        i += 1
    return items or None


def _collect_model_list(
    descriptor: FieldDescriptor,
    existing: list[dict] | None = None,
) -> list[dict] | None:
    """Interactively collect a list of sub-field dicts for *descriptor*.

    Parameters
    ----------
    descriptor : FieldDescriptor
        Field being collected. ``sub_fields`` must be non-empty.
    existing : list[dict] or None, optional
        Current values shown when updating a config.

    Returns
    -------
    list[dict] or None
        Collected items, or None if the user skipped.
    """

    if existing:
        typer.echo(f"  Current {descriptor.label}:")
        for entry in existing:
            typer.echo(f"    {entry}")
        if not ask_yes_no(
            f"  Replace existing {descriptor.label}?", default=False
        ):
            return existing

    items: list[dict] = []
    while True:
        entry: dict = {}
        typer.echo(f"  New {descriptor.label} item:")
        for sub in descriptor.sub_fields:
            val = ask_text(f"    {sub.label} (required):", required=True)
            entry[sub.key] = val
        items.append(entry)
        if not ask_yes_no(
            f"  Add another {descriptor.label} item?", default=False
        ):
            break
    return items or None


def _collect_optional(
    fields: list[FieldDescriptor],
    existing: dict | None = None,
) -> dict:
    """Prompt for a list of optional fields, skipping blanks.

    Parameters
    ----------
    fields : list[FieldDescriptor]
        Field descriptors.
    existing : dict or None, optional
        Pre-populate prompts with existing values.

    Returns
    -------
    dict
        Non-empty field values keyed by field name.
    """

    result: dict = {}
    existing = existing or {}
    for desc in fields:
        if desc.kind == "scalar":
            default = str(existing.get(desc.key, ""))
            skip = " (optional — Enter to skip)"
            suffix = f" ({desc.hint})" if desc.hint else skip
            text = ask_text(f"{desc.label}{suffix}:", default=default)
            if text:
                try:
                    result[desc.key] = desc.cast(text)
                except (ValueError, TypeError):
                    typer.secho(
                        f"  Invalid value for {desc.key!r}; skipping.",
                        fg=typer.colors.YELLOW,
                        err=True,
                    )
        elif desc.kind == "str_list":
            if ask_yes_no(f"Configure {desc.label}?", default=False):
                collected = _collect_str_list(desc, existing.get(desc.key))
                if collected:
                    result[desc.key] = collected
        elif desc.kind == "model_list":
            if ask_yes_no(f"Configure {desc.label}?", default=False):
                collected = _collect_model_list(desc, existing.get(desc.key))
                if collected:
                    result[desc.key] = collected
    return result


def _build_config_interactively(
    existing: dict | None = None,
) -> dict:
    """Walk the user through constructing a full config payload.

    Parameters
    ----------
    existing : dict or None, optional
        Existing config values for pre-population (used by ``update``).

    Returns
    -------
    dict
        Config payload ready to pass to :meth:`~elhaz.config.Config.add`.
    """

    existing = existing or {}
    existing_ar = existing.get("AssumeRole", {})

    role_arn = ask_text(
        "RoleArn (required):",
        default=existing_ar.get("RoleArn", ""),
        required=True,
    )
    assume_role: dict = {"RoleArn": role_arn}

    if ask_yes_no("Configure optional AssumeRole settings?", default=False):
        assume_role.update(
            _collect_optional(_ASSUME_ROLE_OPTIONAL, existing_ar)
        )

    config: dict = {"AssumeRole": assume_role}

    if ask_yes_no("Configure STS client settings?", default=False):
        sts = _collect_optional(_STS_FIELDS, existing.get("STS", {}))
        if sts:
            config["STS"] = sts

    if ask_yes_no("Configure MFA settings?", default=False):
        cmd = ask_text(
            "MFA command (shell command or executable):",
            required=True,
        )
        timeout_str = ask_text("MFA timeout in seconds:", default="30")
        try:
            timeout = int(timeout_str) if timeout_str else 30
        except ValueError:
            timeout = 30
        config["MFA"] = {"command": cmd, "timeout": timeout}

    if ask_yes_no("Configure Session settings?", default=False):
        session = _collect_optional(
            _SESSION_FIELDS, existing.get("Session", {})
        )
        if session:
            config["Session"] = session

    return config


def _open_in_editor(path: "os.PathLike[str]") -> None:
    """Open *path* in the user's ``$EDITOR``, defaulting to ``vi``.

    Parameters
    ----------
    path : os.PathLike[str]
        File to open.
    """

    editor = os.environ.get("EDITOR", "vi")
    subprocess.run([editor, str(path)], check=False)


@app.command("add")
def config_add(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Create a new config in the local config store."""

    if not name:
        name = ask_text("Config name:", required=True)

    cfg = Config(name, state)

    if cfg.file_path.exists():
        if not ask_yes_no(
            f"Config '{name}' already exists. Overwrite?",
            default=False,
        ):
            raise typer.Exit(0)
        cfg.delete()

    if ask_yes_no("Create config interactively?"):
        payload = _build_config_interactively()
        try:
            cfg.add(payload)
            print_success(f"Config '{name}' created.")
        except ElhazAlreadyExistsError as exc:
            print_error(str(exc))
            raise typer.Exit(1)
        except ElhazValidationError as exc:
            print_error(str(exc))
            raise typer.Exit(1)
    else:
        cfg.file_path.parent.mkdir(parents=True, exist_ok=True)
        cfg.file_path.touch()
        _open_in_editor(cfg.file_path)
        typer.echo(f"Config file saved to {cfg.file_path}.")


@app.command("list")
def config_list() -> None:
    """List all config names in the local config store."""

    names = list_local_configs(state)
    if not names:
        typer.echo("No configs found.")
        return
    for name in names:
        typer.echo(name)


@app.command("get")
def config_get(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Return config details as formatted JSON."""

    if not name:
        names = list_local_configs(state)
        if not names:
            typer.secho(
                "No configs found. Run 'elhaz config add' first.",
                fg=typer.colors.YELLOW,
                err=True,
            )
            raise typer.Exit(1)
        name = select_local_config(state, "Select a config:")

    cfg = Config(name, state)

    if not cfg.file_path.exists():
        if ask_yes_no(
            f"Config '{name}' does not exist in the local config "
            "store. Would you like to create it?",
            default=False,
        ):
            config_add(name=name)
        raise typer.Exit(0)

    try:
        print_json(cfg.get())
    except ElhazNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except ElhazValidationError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@app.command("update")
def config_update(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Update a config interactively."""

    name = resolve_name(name, state, message="Select a config to update:")
    cfg = Config(name, state)

    try:
        existing = cfg.get()
    except ElhazNotFoundError:
        print_error(f"Config '{name}' not found.")
        raise typer.Exit(1)
    except ElhazValidationError as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    if ask_yes_no("Edit interactively?"):
        payload = _build_config_interactively(existing)
        try:
            cfg.delete()
            cfg.add(payload)
            print_success(f"Config '{name}' updated.")
        except ElhazValidationError as exc:
            print_error(str(exc))
            raise typer.Exit(1)
    else:
        _open_in_editor(cfg.file_path)
        typer.echo(f"Config file saved to {cfg.file_path}.")


@app.command("remove")
def config_remove(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Remove a config from the local config store."""

    name = resolve_name(name, state, message="Select a config to remove:")
    cfg = Config(name, state)

    if not cfg.file_path.exists():
        print_error(f"Config '{name}' not found.")
        raise typer.Exit(1)

    if not ask_yes_no(
        f"Remove config '{name}'? This cannot be undone.",
        default=False,
    ):
        raise typer.Exit(0)

    cfg.delete()
    print_success(f"Config '{name}' removed.")
