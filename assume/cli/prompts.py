"""Interactive prompt helpers (questionary wrappers)."""

__all__ = []

from collections.abc import Callable
from typing import Optional

import questionary
import typer

from assume.constants import Constants
from assume.daemon import Client
from assume.exceptions import AssumeDaemonError

from .output import print_error


def list_local_configs(constants: Constants) -> list[str]:
    """Return all config names found in ``constants.config_dir``.

    Parameters
    ----------
    constants : Constants
        Provides ``config_dir`` and ``config_file_extension``.

    Returns
    -------
    list[str]
        Sorted config names, or an empty list if the directory is absent.
    """
    if not constants.config_dir.exists():
        return []
    ext = constants.config_file_extension
    return sorted(p.stem for p in constants.config_dir.glob(f"*{ext}"))


def select_local_config(
    constants: Constants,
    message: str = "Select a config:",
) -> str:
    """Prompt the user to pick a config from the local store.

    Parameters
    ----------
    constants : Constants
        Used to locate the config directory.
    message : str, optional
        Prompt text.

    Returns
    -------
    str
        Selected config name. Exits cleanly on Ctrl-C or empty store.
    """
    names = list_local_configs(constants)
    if not names:
        typer.secho(
            "No configs found. Run 'assume config add' to create one.",
            fg=typer.colors.YELLOW,
            err=True,
        )
        raise typer.Exit(1)
    result = questionary.select(message, choices=names).ask()
    if result is None:
        raise typer.Exit(0)
    return result


def select_daemon_session(
    constants: Constants,
    message: str = "Select a session:",
) -> str:
    """Prompt the user to pick an active daemon session.

    Parameters
    ----------
    constants : Constants
        Used to connect to the daemon socket.
    message : str, optional
        Prompt text.

    Returns
    -------
    str
        Selected session name. Exits on error or Ctrl-C.
    """
    try:
        with Client(constants) as client:
            response = client.send("list")
    except AssumeDaemonError as exc:
        print_error(f"Daemon unreachable: {exc}")
        raise typer.Exit(1)

    sessions: list[str] = response.data or []
    if not sessions:
        typer.secho(
            "No active sessions. Run 'assume daemon add' first.",
            fg=typer.colors.YELLOW,
            err=True,
        )
        raise typer.Exit(1)

    result = questionary.select(message, choices=sessions).ask()
    if result is None:
        raise typer.Exit(0)
    return result


def resolve_name(
    name: Optional[str],
    constants: Constants,
    *,
    from_daemon: bool = False,
    message: str = "Select a config:",
) -> str:
    """Return *name* if given; otherwise prompt the user to choose one.

    Parameters
    ----------
    name : str or None
        Explicitly supplied name, or None to trigger a prompt.
    constants : Constants
        Forwarded to the selection helper.
    from_daemon : bool, optional
        If True, select from active daemon sessions; otherwise from the
        local config store.
    message : str, optional
        Prompt text shown to the user.

    Returns
    -------
    str
        Resolved name.
    """
    if name:
        return name
    if from_daemon:
        return select_daemon_session(constants, message)
    return select_local_config(constants, message)


def ask_yes_no(question: str, *, default: bool = True) -> bool:
    """Ask a yes/no question and return the boolean answer.

    Parameters
    ----------
    question : str
        The question to display.
    default : bool, optional
        Pre-selected answer when the user presses Enter.

    Returns
    -------
    bool
        True for yes, False for no. Exits cleanly on Ctrl-C.
    """
    result = questionary.confirm(question, default=default).ask()
    if result is None:
        raise typer.Exit(0)
    return result


def ask_text(
    question: str,
    *,
    default: str = "",
    required: bool = False,
    validate: Optional[Callable[[str], bool | str]] = None,
) -> str:
    """Prompt for a single line of text input.

    Parameters
    ----------
    question : str
        The prompt to display.
    default : str, optional
        Pre-filled value shown to the user.
    required : bool, optional
        If True, reject empty or whitespace-only input.
    validate : callable or None, optional
        Called with the current text; should return True or an error
        string.

    Returns
    -------
    str
        The entered text. Exits cleanly on Ctrl-C.
    """

    def _validator(text: str) -> bool | str:
        if required and not text.strip():
            return "This field is required."
        if validate is not None:
            return validate(text)
        return True

    result = questionary.text(
        question,
        default=default,
        validate=_validator,
    ).ask()
    if result is None:
        raise typer.Exit(0)
    return result
