# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Daemon subcommands: start, stop, logs, list, kill, add, remove."""

import collections
import itertools
import logging
import subprocess
import sys
import time
from typing import Optional

import typer

from elhaz.daemon import (
    Client,
    DaemonService,
    Server,
    configure_daemon_logging,
)
from elhaz.exceptions import ElhazDaemonError

from ..constants import state
from .output import print_error, print_success
from .prompts import resolve_name

app = typer.Typer(
    name="daemon",
    help="Manage the elhaz daemon.",
    no_args_is_help=True,
)


def _is_running() -> bool:
    """Return True if the daemon is reachable on the current socket."""

    try:
        with Client(state) as c:
            c.send("list")
        return True
    except ElhazDaemonError:
        return False


def _wait_until_running(timeout: float = 5.0) -> bool:
    """Poll until the daemon is reachable or *timeout* elapses.

    Parameters
    ----------
    timeout : float, optional
        Seconds to wait before giving up.

    Returns
    -------
    bool
        True if the daemon became reachable within *timeout*.
    """

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _is_running():
            return True
        time.sleep(0.1)
    return False


def _wait_until_stopped(timeout: float = 5.0) -> bool:
    """Poll until the daemon is unreachable or *timeout* elapses.

    Parameters
    ----------
    timeout : float, optional
        Seconds to wait before giving up.

    Returns
    -------
    bool
        True if the daemon became unreachable within *timeout*.
    """

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _is_running():
            return True
        time.sleep(0.1)
    return False


def _daemon_subprocess_cmd() -> list[str]:
    """Build the ``elhaz daemon _serve`` subprocess command.

    Forwards all current Constants values so the daemon process uses
    the same configuration as the CLI invocation.

    Returns
    -------
    list[str]
        Argv for :func:`subprocess.Popen`.
    """

    return [
        sys.executable,
        "-m",
        "elhaz.cli",
        "--socket-path",
        str(state.socket_path),
        "--logging-path",
        str(state.daemon_logging_path),
        "--config-dir",
        str(state.config_dir),
        "--max-unix-socket-connections",
        str(state.max_unix_socket_connections),
        "--max-daemon-cache-size",
        str(state.max_daemon_cache_size),
        "--client-timeout",
        str(state.client_timeout),
        "daemon",
        "_serve",
    ]


@app.command("status")
def daemon_status() -> None:
    """Report whether the daemon is currently running.

    Exits with code 0 if the daemon is reachable, 1 if it is not.
    """

    if _is_running():
        typer.secho("Daemon is running.", fg=typer.colors.GREEN)
        typer.echo(f"  Socket: {state.socket_path}")
    else:
        typer.secho("Daemon is not running.", fg=typer.colors.YELLOW)
        raise typer.Exit(1)


@app.command("start")
def daemon_start() -> None:
    """Start the daemon in the background."""

    if _is_running():
        typer.echo("Daemon is already running.")
        return

    subprocess.Popen(
        _daemon_subprocess_cmd(),
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    if _wait_until_running():
        print_success("Daemon started.")
        typer.echo(f"  Socket:  {state.socket_path}")
        typer.echo(f"  Log:     {state.daemon_logging_path}")
    else:
        print_error(
            "Daemon did not start within 5 seconds. "
            f"Check the log file: {state.daemon_logging_path}"
        )
        raise typer.Exit(1)


@app.command("stop")
def daemon_stop() -> None:
    """Stop the running daemon gracefully."""

    if not _is_running():
        typer.echo("Daemon is not running.")
        return

    try:
        with Client(state) as client:
            response = client.send("kill")
    except ElhazDaemonError as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    if not response.ok:
        print_error(
            response.error.message if response.error else "Unknown error."
        )
        raise typer.Exit(1)

    if _wait_until_stopped():
        print_success("Daemon stopped.")
    else:
        print_error("Daemon did not stop within 5 seconds.")
        raise typer.Exit(1)


@app.command("kill")
def daemon_kill() -> None:
    """Forcefully stop the daemon (alias for ``stop``)."""

    daemon_stop()


@app.command("logs")
def daemon_logs(
    tail: Optional[int] = typer.Option(
        50,
        "--tail",
        "-t",
        help="Show the last N lines (default: 50).",
    ),
    head: Optional[int] = typer.Option(
        None,
        "--head",
        "-h",
        help="Show the first N lines.",
    ),
) -> None:
    """Print daemon log output.

    Defaults to the last 50 lines. Use ``--head`` for the first N
    lines, or ``--tail 0`` to stream the entire file.
    """

    path = state.daemon_logging_path

    if not path.exists():
        typer.echo("No log file found.")
        return

    if head is not None:
        with open(path, encoding="utf-8") as f:
            for line in itertools.islice(f, head):
                typer.echo(line, nl=False)
    else:
        n = tail if tail and tail > 0 else None
        with open(path, encoding="utf-8") as f:
            for line in collections.deque(f, maxlen=n):
                typer.echo(line, nl=False)


@app.command("list")
def daemon_list() -> None:
    """List all active sessions in the daemon's cache."""

    try:
        with Client(state) as client:
            response = client.send("list")
    except ElhazDaemonError as exc:
        print_error(f"Daemon unreachable: {exc}")
        raise typer.Exit(1)

    if not response.ok:
        print_error(
            response.error.message if response.error else "Unknown error."
        )
        raise typer.Exit(1)

    sessions: list[str] = response.data or []
    if not sessions:
        typer.echo("No active sessions.")
        return
    for name in sessions:
        typer.echo(name)


@app.command("add")
def daemon_add(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Initialize an AWS session and add it to the daemon's cache."""

    name = resolve_name(name, state, message="Select a config:")

    try:
        with Client(state) as client:
            response = client.send("add", {"config": name})
    except ElhazDaemonError as exc:
        print_error(f"Daemon unreachable: {exc}")
        raise typer.Exit(1)

    if not response.ok:
        print_error(
            response.error.message if response.error else "Unknown error."
        )
        raise typer.Exit(1)

    print_success(f"Session '{name}' added to daemon cache.")


@app.command("remove")
def daemon_remove(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Config name."
    ),
) -> None:
    """Remove an active session from the daemon's cache."""

    name = resolve_name(
        name,
        state,
        from_daemon=True,
        message="Select a session to remove:",
    )

    try:
        with Client(state) as client:
            response = client.send("remove", {"config": name})
    except ElhazDaemonError as exc:
        print_error(f"Daemon unreachable: {exc}")
        raise typer.Exit(1)

    if not response.ok:
        print_error(
            response.error.message if response.error else "Unknown error."
        )
        raise typer.Exit(1)

    print_success(f"Session '{name}' removed from daemon cache.")


@app.command("_serve", hidden=True)
def daemon_serve() -> None:
    """Start the daemon server (internal; invoked by ``daemon start``)."""

    configure_daemon_logging(state)

    _log = logging.getLogger(__name__)

    try:
        service = DaemonService(max_size=state.max_daemon_cache_size)
        server = Server(state, service)
        server.run()
    except Exception:
        # stderr is /dev/null in the detached subprocess, so any startup
        # or runtime exception must be written to the log file explicitly.
        _log.exception("Daemon process failed.")
        raise
