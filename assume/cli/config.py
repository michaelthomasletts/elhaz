# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Config subcommands: add, list, get, update, remove."""

import os
import subprocess
from typing import Optional

import typer

from assume.config import Config
from assume.exceptions import (
    AssumeAlreadyExistsError,
    AssumeNotFoundError,
    AssumeValidationError,
)

from .output import print_error, print_json, print_success
from .prompts import (
    ask_text,
    ask_yes_no,
    list_local_configs,
    resolve_name,
    select_local_config,
)
from .state import state

app = typer.Typer(
    name="config",
    help="Manage assume configurations.",
    no_args_is_help=True,
)


# (key, prompt label, cast, hint)
_ASSUME_ROLE_OPTIONAL: list[tuple[str, str, type, str | None]] = [
    ("RoleSessionName", "RoleSessionName", str, None),
    ("DurationSeconds", "DurationSeconds", int, "seconds"),
    ("ExternalId", "ExternalId", str, None),
    ("SerialNumber", "SerialNumber (MFA device ARN)", str, None),
    ("TokenCode", "TokenCode (MFA token)", str, None),
    ("SourceIdentity", "SourceIdentity", str, None),
    ("Policy", "Inline session policy (JSON string)", str, None),
]

_STS_FIELDS: list[tuple[str, str, type, str | None]] = [
    ("region_name", "Region name", str, None),
    ("endpoint_url", "STS endpoint URL", str, None),
    ("api_version", "API version", str, None),
]

_SESSION_FIELDS: list[tuple[str, str, type, str | None]] = [
    ("region_name", "Region name", str, None),
    ("profile_name", "AWS profile name", str, None),
]


def _collect_optional(
    fields: list[tuple[str, str, type, str | None]],
    existing: dict | None = None,
) -> dict:
    """Prompt for a list of optional fields, skipping blanks.

    Parameters
    ----------
    fields : list of (key, label, cast, hint)
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
    for key, label, cast, hint in fields:
        default = str(existing.get(key, ""))
        suffix = f" ({hint})" if hint else " (optional — Enter to skip)"
        text = ask_text(f"{label}{suffix}:", default=default)
        if text:
            try:
                result[key] = cast(text)
            except (ValueError, TypeError):
                typer.secho(
                    f"  Invalid value for {key!r}; skipping.",
                    fg=typer.colors.YELLOW,
                    err=True,
                )
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
        Config payload ready to pass to :meth:`~assume.config.Config.add`.
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

    constants = state.constants

    if not name:
        name = ask_text("Config name:", required=True)

    cfg = Config(name, constants)

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
        except AssumeAlreadyExistsError as exc:
            print_error(str(exc))
            raise typer.Exit(1)
        except AssumeValidationError as exc:
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

    names = list_local_configs(state.constants)
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

    constants = state.constants

    if not name:
        names = list_local_configs(constants)
        if not names:
            typer.secho(
                "No configs found. Run 'assume config add' first.",
                fg=typer.colors.YELLOW,
                err=True,
            )
            raise typer.Exit(1)
        name = select_local_config(constants, "Select a config:")

    cfg = Config(name, constants)

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
    except AssumeNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except AssumeValidationError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@app.command("update")
def config_update(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Update a config interactively."""

    constants = state.constants
    name = resolve_name(name, constants, message="Select a config to update:")
    cfg = Config(name, constants)

    try:
        existing = cfg.get()
    except AssumeNotFoundError:
        print_error(f"Config '{name}' not found.")
        raise typer.Exit(1)
    except AssumeValidationError as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    if ask_yes_no("Edit interactively?"):
        payload = _build_config_interactively(existing)
        try:
            cfg.delete()
            cfg.add(payload)
            print_success(f"Config '{name}' updated.")
        except AssumeValidationError as exc:
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

    constants = state.constants
    name = resolve_name(name, constants, message="Select a config to remove:")
    cfg = Config(name, constants)

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
