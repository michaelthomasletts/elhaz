# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.cli.output."""

from __future__ import annotations

import datetime
import json

from elhaz.cli.output import print_error, print_json, print_success


def test_print_json_non_tty_outputs_plain_json(capsys) -> None:
    data = {"key": "value", "num": 42}
    print_json(data)
    captured = capsys.readouterr()
    # In test environment stdout is not a TTY, so plain JSON expected.
    parsed = json.loads(captured.out)
    assert parsed == data


def test_print_json_non_tty_uses_indent_2(capsys) -> None:
    data = {"a": 1}
    print_json(data)
    captured = capsys.readouterr()
    assert "  " in captured.out  # indented


def test_print_json_serializes_non_native_types_via_str(capsys) -> None:
    dt = datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc)
    data = {"ts": dt}
    print_json(data)
    captured = capsys.readouterr()
    assert "2030" in captured.out


def test_print_json_nothing_to_stderr(capsys) -> None:
    print_json({"x": 1})
    captured = capsys.readouterr()
    assert captured.err == ""


def test_print_json_tty_calls_typer_echo(monkeypatch, capsys) -> None:
    """When stdout is a TTY, output goes through pygments highlight."""
    import sys

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    # We just check that something is written to stdout without crashing
    print_json({"hello": "world"})
    captured = capsys.readouterr()
    # Highlighted output is non-empty (contains some content)
    assert len(captured.out) > 0


def test_print_error_goes_to_stderr(capsys) -> None:
    print_error("something broke")
    captured = capsys.readouterr()
    assert "Error: something broke" in captured.err


def test_print_error_nothing_to_stdout(capsys) -> None:
    print_error("oops")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_print_error_has_error_prefix(capsys) -> None:
    print_error("my message")
    captured = capsys.readouterr()
    assert captured.err.startswith("Error:")


def test_print_success_goes_to_stdout(capsys) -> None:
    print_success("everything worked")
    captured = capsys.readouterr()
    assert "everything worked" in captured.out


def test_print_success_nothing_to_stderr(capsys) -> None:
    print_success("done")
    captured = capsys.readouterr()
    assert captured.err == ""
