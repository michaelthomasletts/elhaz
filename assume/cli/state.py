"""Module-level CLI state shared across all subcommands."""

__all__ = []

from assume.constants import Constants


class _State:
    """Mutable singleton holding CLI-wide configuration.

    The ``constants`` attribute is modified by the main callback when
    the user passes global options (``--socket-path``, etc.). All
    subcommands read from it without needing typer context plumbing.
    """

    def __init__(self) -> None:
        self.constants: Constants = Constants()


state: _State = _State()
