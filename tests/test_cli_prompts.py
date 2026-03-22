# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.cli.prompts."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import typer

from elhaz.constants import Constants
from elhaz.exceptions import ElhazDaemonError
from tests.conftest import ok_response


def test_list_local_configs_returns_empty_when_dir_absent(
    tmp_constants: Constants,
) -> None:
    from elhaz.cli.prompts import list_local_configs

    assert list_local_configs(tmp_constants) == []


def test_list_local_configs_returns_sorted_stems(
    tmp_constants: Constants,
) -> None:
    from elhaz.cli.prompts import list_local_configs

    tmp_constants.config_dir.mkdir(parents=True, exist_ok=True)
    for name in ("charlie", "alpha", "beta"):
        (tmp_constants.config_dir / f"{name}.yaml").touch()

    result = list_local_configs(tmp_constants)
    assert result == ["alpha", "beta", "charlie"]


def test_list_local_configs_ignores_wrong_extension(
    tmp_constants: Constants,
) -> None:
    from elhaz.cli.prompts import list_local_configs

    tmp_constants.config_dir.mkdir(parents=True, exist_ok=True)
    (tmp_constants.config_dir / "good.yaml").touch()
    (tmp_constants.config_dir / "bad.json").touch()
    (tmp_constants.config_dir / "also_bad.txt").touch()

    result = list_local_configs(tmp_constants)
    assert result == ["good"]


def test_list_local_configs_empty_directory(
    tmp_constants: Constants,
) -> None:
    from elhaz.cli.prompts import list_local_configs

    tmp_constants.config_dir.mkdir(parents=True, exist_ok=True)
    assert list_local_configs(tmp_constants) == []


def test_resolve_name_returns_provided_name_directly(
    tmp_constants: Constants,
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    called = {"select_local": False, "select_daemon": False}
    monkeypatch.setattr(
        prompts,
        "select_local_config",
        lambda *a, **k: called.__setitem__("select_local", True) or "x",
    )
    monkeypatch.setattr(
        prompts,
        "select_daemon_session",
        lambda *a, **k: called.__setitem__("select_daemon", True) or "x",
    )

    result = prompts.resolve_name("explicit", tmp_constants)
    assert result == "explicit"
    assert not called["select_local"]
    assert not called["select_daemon"]


def test_resolve_name_none_from_daemon_false_calls_select_local(
    tmp_constants: Constants,
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    monkeypatch.setattr(
        prompts, "select_local_config", lambda c, msg="": "local-choice"
    )
    result = prompts.resolve_name(None, tmp_constants, from_daemon=False)
    assert result == "local-choice"


def test_resolve_name_none_from_daemon_true_calls_select_daemon(
    tmp_constants: Constants,
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    monkeypatch.setattr(
        prompts, "select_daemon_session", lambda c, msg="": "daemon-choice"
    )
    result = prompts.resolve_name(None, tmp_constants, from_daemon=True)
    assert result == "daemon-choice"


def test_ask_yes_no_returns_true(monkeypatch) -> None:
    from elhaz.cli import prompts

    mock_confirm = MagicMock()
    mock_confirm.return_value.ask.return_value = True
    monkeypatch.setattr(prompts.questionary, "confirm", mock_confirm)

    result = prompts.ask_yes_no("Are you sure?")
    assert result is True


def test_ask_yes_no_returns_false(monkeypatch) -> None:
    from elhaz.cli import prompts

    mock_confirm = MagicMock()
    mock_confirm.return_value.ask.return_value = False
    monkeypatch.setattr(prompts.questionary, "confirm", mock_confirm)

    result = prompts.ask_yes_no("Are you sure?")
    assert result is False


def test_ask_yes_no_ctrl_c_raises_exit_0(monkeypatch) -> None:
    from elhaz.cli import prompts

    mock_confirm = MagicMock()
    mock_confirm.return_value.ask.return_value = None
    monkeypatch.setattr(prompts.questionary, "confirm", mock_confirm)

    with pytest.raises(typer.Exit) as exc_info:
        prompts.ask_yes_no("Are you sure?")
    assert exc_info.value.exit_code == 0


def test_ask_text_returns_text(monkeypatch) -> None:
    from elhaz.cli import prompts

    mock_text = MagicMock()
    mock_text.return_value.ask.return_value = "hello"
    monkeypatch.setattr(prompts.questionary, "text", mock_text)

    result = prompts.ask_text("Enter something:")
    assert result == "hello"


def test_ask_text_ctrl_c_raises_exit_0(monkeypatch) -> None:
    from elhaz.cli import prompts

    mock_text = MagicMock()
    mock_text.return_value.ask.return_value = None
    monkeypatch.setattr(prompts.questionary, "text", mock_text)

    with pytest.raises(typer.Exit) as exc_info:
        prompts.ask_text("Enter something:")
    assert exc_info.value.exit_code == 0


def test_ask_text_required_validator_empty_returns_error(
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    captured_validator = {}

    def _fake_text(question, default="", validate=None):
        captured_validator["fn"] = validate
        mock = MagicMock()
        mock.ask.return_value = "valid input"
        return mock

    monkeypatch.setattr(prompts.questionary, "text", _fake_text)
    prompts.ask_text("Q:", required=True)

    validator = captured_validator["fn"]
    assert validator("") == "This field is required."
    assert validator("   ") == "This field is required."


def test_ask_text_required_validator_non_empty_returns_true(
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    captured_validator = {}

    def _fake_text(question, default="", validate=None):
        captured_validator["fn"] = validate
        mock = MagicMock()
        mock.ask.return_value = "hello"
        return mock

    monkeypatch.setattr(prompts.questionary, "text", _fake_text)
    prompts.ask_text("Q:", required=True)

    validator = captured_validator["fn"]
    assert validator("something") is True


def test_ask_text_custom_validate_is_invoked(monkeypatch) -> None:
    from elhaz.cli import prompts

    captured_validator = {}

    def _fake_text(question, default="", validate=None):
        captured_validator["fn"] = validate
        mock = MagicMock()
        mock.ask.return_value = "hello"
        return mock

    monkeypatch.setattr(prompts.questionary, "text", _fake_text)

    custom_called = {"yes": False}

    def _custom(text: str):
        custom_called["yes"] = True
        return True

    prompts.ask_text("Q:", validate=_custom)
    validator = captured_validator["fn"]
    validator("any")
    assert custom_called["yes"]


def test_select_local_config_empty_store_raises_exit_1(
    tmp_constants: Constants,
) -> None:
    from elhaz.cli.prompts import select_local_config

    with pytest.raises(typer.Exit) as exc_info:
        select_local_config(tmp_constants)
    assert exc_info.value.exit_code == 1


def test_select_local_config_returns_selected_name(
    tmp_constants: Constants,
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    tmp_constants.config_dir.mkdir(parents=True, exist_ok=True)
    (tmp_constants.config_dir / "demo.yaml").touch()

    mock_select = MagicMock()
    mock_select.return_value.ask.return_value = "demo"
    monkeypatch.setattr(prompts.questionary, "select", mock_select)

    result = prompts.select_local_config(tmp_constants)
    assert result == "demo"


def test_select_local_config_ctrl_c_raises_exit_0(
    tmp_constants: Constants,
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    tmp_constants.config_dir.mkdir(parents=True, exist_ok=True)
    (tmp_constants.config_dir / "demo.yaml").touch()

    mock_select = MagicMock()
    mock_select.return_value.ask.return_value = None
    monkeypatch.setattr(prompts.questionary, "select", mock_select)

    with pytest.raises(typer.Exit) as exc_info:
        prompts.select_local_config(tmp_constants)
    assert exc_info.value.exit_code == 0


def test_select_daemon_session_daemon_unreachable_raises_exit_1(
    tmp_constants: Constants,
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    class _BrokenClient:
        def __init__(self, constants):
            raise ElhazDaemonError("no daemon")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    monkeypatch.setattr(prompts, "Client", _BrokenClient)

    with pytest.raises(typer.Exit) as exc_info:
        prompts.select_daemon_session(tmp_constants)
    assert exc_info.value.exit_code == 1


def test_select_daemon_session_no_sessions_raises_exit_1(
    tmp_constants: Constants,
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    class _EmptyClient:
        def __init__(self, constants):
            pass

        def send(self, action, payload=None):
            return ok_response(data=[])

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    monkeypatch.setattr(prompts, "Client", _EmptyClient)

    with pytest.raises(typer.Exit) as exc_info:
        prompts.select_daemon_session(tmp_constants)
    assert exc_info.value.exit_code == 1


def test_select_daemon_session_returns_selected_name(
    tmp_constants: Constants,
    monkeypatch,
) -> None:
    from elhaz.cli import prompts

    class _PopulatedClient:
        def __init__(self, constants):
            pass

        def send(self, action, payload=None):
            return ok_response(data=["demo"])

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    monkeypatch.setattr(prompts, "Client", _PopulatedClient)

    mock_select = MagicMock()
    mock_select.return_value.ask.return_value = "demo"
    monkeypatch.setattr(prompts.questionary, "select", mock_select)

    result = prompts.select_daemon_session(tmp_constants)
    assert result == "demo"
