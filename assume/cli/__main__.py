"""CLI entry point for assume-cli.

Usage
-----
assume [OPTIONS] COMMAND [ARGS]...

Global options modify :class:`~assume.constants.Constants` before any
subcommand runs.  They are forwarded verbatim to ``daemon _serve`` when
starting the background daemon process so both sides share the same
configuration.
"""

__all__: list[str] = []

import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from assume.constants import Constants
from assume.daemon import Client
from assume.exceptions import AssumeDaemonError
from assume.models import CredentialProcessModel

from .config import app as _config_app
from .daemon import app as _daemon_app
from .output import print_error, print_json
from .prompts import ask_yes_no, resolve_name
from .state import state

app = typer.Typer(
    name="assume",
    help="Manage refreshable AWS credentials via a local daemon.",
    no_args_is_help=True,
)

app.add_typer(_config_app, name="config")
app.add_typer(_daemon_app, name="daemon")


@app.callback()
def _callback(
    config_dir: Optional[Path] = typer.Option(
        None,
        "--config-dir",
        "-cd",
        help=(f"Config directory. Default: {Constants._config_dir}"),
        show_default=False,
    ),
    config_file_extension: Optional[str] = typer.Option(
        None,
        "--config-file-extension",
        "-cfe",
        help=(
            "Config file extension. "
            f"Default: {Constants._config_file_extension}"
        ),
        show_default=False,
    ),
    socket_path: Optional[Path] = typer.Option(
        None,
        "--socket-path",
        "-sp",
        help="UNIX socket path for daemon communication.",
        show_default=False,
    ),
    logging_path: Optional[Path] = typer.Option(
        None,
        "--logging-path",
        "-lp",
        help=(
            f"Daemon log file path. Default: {Constants._daemon_logging_path}"
        ),
        show_default=False,
    ),
    max_unix_socket_connections: Optional[int] = typer.Option(
        None,
        "--max-unix-socket-connections",
        "-musc",
        help="Max pending socket connections.",
        show_default=False,
    ),
) -> None:
    """assume — manage refreshable AWS credentials."""
    if config_dir is not None:
        state.constants.config_dir = config_dir
    if config_file_extension is not None:
        state.constants.config_file_extension = config_file_extension
    if socket_path is not None:
        state.constants.socket_path = socket_path
    if logging_path is not None:
        state.constants.daemon_logging_path = logging_path
    if max_unix_socket_connections is not None:
        state.constants.max_unix_socket_connections = (
            max_unix_socket_connections
        )


def _fetch_credentials(name: str) -> dict:
    """Fetch credentials for *name* from the daemon.

    If the session is not cached, adds it first, then retries.

    Parameters
    ----------
    name : str
        Config / session name.

    Returns
    -------
    dict
        Raw credentials dict from the daemon.
    """
    constants = state.constants

    def _send_credentials() -> dict | None:
        try:
            with Client(constants) as client:
                resp = client.send("credentials", {"config": name})
        except AssumeDaemonError as exc:
            print_error(f"Daemon unreachable: {exc}")
            raise typer.Exit(1)
        if resp.ok:
            return resp.data
        return None

    creds = _send_credentials()
    if creds is not None:
        return creds

    # Session not cached — add it, then retry once.
    try:
        with Client(constants) as client:
            add_resp = client.send("add", {"config": name})
    except AssumeDaemonError as exc:
        print_error(f"Daemon unreachable: {exc}")
        raise typer.Exit(1)

    if not add_resp.ok:
        msg = add_resp.error.message if add_resp.error else "Unknown error."
        print_error(msg)
        raise typer.Exit(1)

    creds = _send_credentials()
    if creds is None:
        print_error(f"Could not retrieve credentials for '{name}'.")
        raise typer.Exit(1)
    return creds


class ExportFormat(str, Enum):
    """Available output formats for ``assume export``."""

    json = "json"
    env = "env"
    credential_process = "credential-process"


@app.command("export")
def export_cmd(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
    fmt: ExportFormat = typer.Option(
        ExportFormat.json,
        "--format",
        "-f",
        help="Output format: json | env | credential-process.",
    ),
) -> None:
    """Export credentials for the specified config.

    ``--format json`` (default) prints the raw credentials dict.

    ``--format env`` prints ``export KEY=VALUE`` lines suitable for
    ``eval $(assume export --format env -n myconfig)``.

    ``--format credential-process`` prints the JSON shape required by
    AWS ``credential_process`` profile entries.
    """
    constants = state.constants
    name = resolve_name(name, constants, message="Select a config:")
    creds = _fetch_credentials(name)

    if fmt == ExportFormat.json:
        print_json(creds)

    elif fmt == ExportFormat.env:
        lines = [
            f"export AWS_ACCESS_KEY_ID={creds['access_key']}",
            f"export AWS_SECRET_ACCESS_KEY={creds['secret_key']}",
            f"export AWS_SESSION_TOKEN={creds['token']}",
            (f"export AWS_CREDENTIAL_EXPIRATION={creds['expiry_time']}"),
        ]
        typer.echo("\n".join(lines))

    else:  # credential-process
        model = CredentialProcessModel(
            AccessKeyId=creds["access_key"],
            SecretAccessKey=creds["secret_key"],
            SessionToken=creds["token"],
            Expiration=creds["expiry_time"],
        )
        typer.echo(model.model_dump_json())


@app.command(
    name="exec",
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def exec_cmd(
    ctx: typer.Context,
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Execute a one-off command with AWS credentials as env vars.

    Example:

        assume exec -n myconfig -- aws s3 ls
    """
    constants = state.constants
    name = resolve_name(name, constants, message="Select a config:")

    command = ctx.args
    if not command:
        print_error("No command specified. Usage: assume exec -n NAME -- CMD")
        raise typer.Exit(1)

    creds = _fetch_credentials(name)
    env = os.environ.copy()
    env.update(
        {
            "AWS_ACCESS_KEY_ID": creds["access_key"],
            "AWS_SECRET_ACCESS_KEY": creds["secret_key"],
            "AWS_SESSION_TOKEN": creds["token"],
        }
    )

    result = subprocess.run(command, env=env)
    raise typer.Exit(result.returncode)


@app.command("shell")
def shell_cmd(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Spawn an interactive shell with auto-refreshed AWS credentials.

    Initial credentials are exported as environment variables.
    ``AWS_CREDENTIAL_PROCESS`` is also set so AWS SDKs transparently
    fetch fresh credentials from the daemon on every API call.

    For bash/sh, ``PROMPT_COMMAND`` is set to re-export credentials
    before each prompt so the env vars stay current.
    """
    constants = state.constants
    name = resolve_name(name, constants, message="Select a config:")
    creds = _fetch_credentials(name)

    shell = os.environ.get("SHELL", "/bin/bash")
    shell_name = Path(shell).name

    # Build the credential-process command that points at the daemon.
    cp_cmd = (
        f"{sys.executable} -m assume.cli"
        f" --socket-path {constants.socket_path}"
        f" export --format credential-process -n {name}"
    )

    # Shell hook that re-exports env-var credentials before each prompt.
    refresh_cmd = (
        f"eval $({sys.executable} -m assume.cli"
        f" --socket-path {constants.socket_path}"
        f" export --format env -n {name})"
    )

    env = os.environ.copy()
    env.update(
        {
            "AWS_ACCESS_KEY_ID": creds["access_key"],
            "AWS_SECRET_ACCESS_KEY": creds["secret_key"],
            "AWS_SESSION_TOKEN": creds["token"],
            "AWS_CREDENTIAL_EXPIRATION": creds["expiry_time"],
            "AWS_CREDENTIAL_PROCESS": cp_cmd,
        }
    )

    if shell_name in ("bash", "sh"):
        existing = env.get("PROMPT_COMMAND", "")
        env["PROMPT_COMMAND"] = (
            f"{refresh_cmd}; {existing}" if existing else refresh_cmd
        )
    elif shell_name == "zsh":
        # zsh does not honour PROMPT_COMMAND natively; expose the
        # command via ASSUME_PRECMD so the user can wire it up.
        env["ASSUME_PRECMD"] = refresh_cmd
        typer.secho(
            "  Tip: add 'eval $ASSUME_PRECMD' to your precmd_functions"
            " for automatic env-var refresh in zsh.",
            fg=typer.colors.BLUE,
            err=True,
        )

    typer.secho(
        f"Spawning {shell} with credentials for '{name}'.",
        fg=typer.colors.GREEN,
    )
    typer.secho(
        "  AWS_CREDENTIAL_PROCESS is set for automatic SDK refresh.",
        fg=typer.colors.BLUE,
    )

    result = subprocess.run([shell], env=env)
    raise typer.Exit(result.returncode)


@app.command("whoami")
def whoami_cmd(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Return the STS caller identity for the specified config."""
    constants = state.constants
    name = resolve_name(name, constants, message="Select a config:")

    try:
        with Client(constants) as client:
            response = client.send("whoami", {"config": name})
    except AssumeDaemonError as exc:
        print_error(f"Daemon unreachable: {exc}")
        raise typer.Exit(1)

    if not response.ok:
        code = response.error.code if response.error else None
        if code == 404:
            if ask_yes_no(
                f"No active session for '{name}'. Add it to the daemon?",
            ):
                try:
                    with Client(constants) as client:
                        add_resp = client.send("add", {"config": name})
                except AssumeDaemonError as exc:
                    print_error(f"Daemon unreachable: {exc}")
                    raise typer.Exit(1)
                if not add_resp.ok:
                    msg = (
                        add_resp.error.message
                        if add_resp.error
                        else "Unknown error."
                    )
                    print_error(msg)
                    raise typer.Exit(1)
                whoami_cmd(name=name)
                return
        else:
            msg = (
                response.error.message if response.error else "Unknown error."
            )
            print_error(msg)
        raise typer.Exit(1)

    print_json(response.data)


def main() -> None:
    """Package entry point (``assume.cli.__main__:main``)."""
    app()


if __name__ == "__main__":
    main()
