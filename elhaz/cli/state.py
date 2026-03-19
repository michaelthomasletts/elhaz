# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Module-level CLI state shared across all subcommands."""

from elhaz.constants import Constants


class _State:
    """Mutable singleton holding CLI-wide configuration.

    The ``constants`` attribute is modified by the main callback when
    the user passes global options (``--socket-path``, etc.). All
    subcommands read from it without needing typer context plumbing.
    """

    def __init__(self) -> None:
        self.constants: Constants = Constants()


state: _State = _State()
