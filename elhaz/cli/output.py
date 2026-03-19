# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Output helpers: pygments-highlighted JSON and status messages."""

import json
import sys
from typing import Any

import typer
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import JsonLexer

_FORMATTER = Terminal256Formatter(style="monokai")


def print_json(data: Any) -> None:
    """Pretty-print *data* as syntax-highlighted JSON.

    Falls back to plain JSON when stdout is not a TTY (e.g. pipes).

    Parameters
    ----------
    data : Any
        JSON-serializable value to display.
    """

    formatted = json.dumps(data, indent=2, default=str)
    if sys.stdout.isatty():
        typer.echo(
            highlight(formatted, JsonLexer(), _FORMATTER),
            nl=False,
        )
    else:
        typer.echo(formatted)


def print_error(message: str) -> None:
    """Print *message* to stderr in red.

    Parameters
    ----------
    message : str
        Error description.
    """

    typer.secho(f"Error: {message}", fg=typer.colors.RED, err=True)


def print_success(message: str) -> None:
    """Print *message* to stdout in green.

    Parameters
    ----------
    message : str
        Success description.
    """

    typer.secho(message, fg=typer.colors.GREEN)
