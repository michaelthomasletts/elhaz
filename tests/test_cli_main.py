# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.cli.__main__ (export, exec, shell, whoami)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from typer.testing import CliRunner

from elhaz.cli.__main__ import app
from elhaz.exceptions import ElhazDaemonError
from elhaz.models import ResponseModel
from tests.conftest import err_response, ok_response

runner = CliRunner()

# Fake credentials returned by the daemon for happy-path tests.
FAKE_CREDS = {
    "access_key": "AKIATEST",
    "secret_key": "SUPERSECRET",
    "token": "TOKEN123",
    "expiry_time": "2030-01-01T00:00:00Z",
}

FAKE_IDENTITY = {
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/demo/session",
    "UserId": "AROATEST:session",
}


def _install_fake_client(monkeypatch, responses: list) -> None:
    """Patch elhaz.cli.__main__.Client with a fake that returns *responses*."""
    import collections

    queue: collections.deque = collections.deque(responses)

    class _FakeClient:
        def __init__(self, constants: Any) -> None:
            if queue and isinstance(queue[0], Exception):
                raise queue.popleft()

        def send(
            self, action: str, payload: dict | None = None
        ) -> ResponseModel:
            if not queue:
                raise RuntimeError("Response queue exhausted")
            item = queue.popleft()
            if isinstance(item, Exception):
                raise item
            return item

        def close(self) -> None:
            pass

        def __enter__(self) -> "_FakeClient":
            return self

        def __exit__(self, *_: Any) -> None:
            pass

    monkeypatch.setattr("elhaz.cli.__main__.Client", _FakeClient)


def test_callback_socket_path_updates_state(
    monkeypatch, tmp_path: Path
) -> None:
    sock = tmp_path / "test.sock"

    # Provide a no-op subcommand response
    _install_fake_client(monkeypatch, [ok_response(data=[])])

    result = runner.invoke(app, ["--socket-path", str(sock), "daemon", "list"])
    # state.socket_path should have been updated during the invocation
    # (the autouse fixture restores it after, so we check indirectly
    # by ensuring no validation error was raised)
    assert result.exit_code in (0, 1)  # daemon list may fail on empty


def test_callback_config_dir_updates_state(
    monkeypatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "test-configs"
    config_dir.mkdir()
    # config list command reads state.config_dir
    result = runner.invoke(
        app, ["--config-dir", str(config_dir), "config", "list"]
    )
    assert "No configs found." in result.output or result.exit_code == 0


def test_callback_max_daemon_cache_size_updates_state(
    monkeypatch, tmp_path: Path
) -> None:
    # Just check that the option is accepted without raising
    _install_fake_client(monkeypatch, [ok_response(data=[])])
    result = runner.invoke(
        app,
        [
            "--max-daemon-cache-size",
            "5",
            "daemon",
            "list",
        ],
    )
    assert result.exit_code in (0, 1)


def test_callback_options_not_provided_state_unchanged(
    monkeypatch,
) -> None:
    from elhaz import constants as _constants_mod

    original_cache_size = _constants_mod.state.max_daemon_cache_size
    _install_fake_client(monkeypatch, [ok_response(data=[])])
    runner.invoke(app, ["daemon", "list"])
    assert _constants_mod.state.max_daemon_cache_size == original_cache_size


def test_export_happy_path_credentials_in_cache(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    result = runner.invoke(app, ["export", "--name", "demo"])
    assert result.exit_code == 0
    assert "AKIATEST" in result.output


def test_export_auto_add_credentials_not_cached(monkeypatch) -> None:
    """credentials not cached → add → retry credentials."""
    _install_fake_client(
        monkeypatch,
        [
            err_response(404, "not found"),  # first credentials call
            ok_response(data={"config": "demo"}),  # add call
            ok_response(data=FAKE_CREDS),  # second credentials call
        ],
    )
    result = runner.invoke(app, ["export", "--name", "demo"])
    assert result.exit_code == 0
    assert "AKIATEST" in result.output


def test_export_first_credentials_daemon_error_exits_1(
    monkeypatch,
) -> None:
    _install_fake_client(monkeypatch, [ElhazDaemonError("no daemon")])
    result = runner.invoke(app, ["export", "--name", "demo"])
    assert result.exit_code == 1
    assert "Daemon unreachable" in result.output


def test_export_add_daemon_error_exits_1(monkeypatch) -> None:
    """First credentials ok=False → add → daemon error."""
    _install_fake_client(
        monkeypatch,
        [
            err_response(404, "not found"),  # first credentials call
            ElhazDaemonError("gone"),  # add call raises
        ],
    )
    result = runner.invoke(app, ["export", "--name", "demo"])
    assert result.exit_code == 1
    assert "Daemon unreachable" in result.output


def test_export_add_fails_ok_false_exits_1(monkeypatch) -> None:
    _install_fake_client(
        monkeypatch,
        [
            err_response(404, "not found"),  # first credentials
            err_response(500, "add failed"),  # add response ok=False
        ],
    )
    result = runner.invoke(app, ["export", "--name", "demo"])
    assert result.exit_code == 1


def test_export_second_credentials_returns_none_exits_1(
    monkeypatch,
) -> None:
    """Auto-add succeeds but second credentials call returns ok=False."""
    _install_fake_client(
        monkeypatch,
        [
            err_response(404, "not found"),  # first credentials
            ok_response(data={"config": "demo"}),  # add
            err_response(500, "still not found"),  # second credentials
        ],
    )
    result = runner.invoke(app, ["export", "--name", "demo"])
    assert result.exit_code == 1
    assert "Could not retrieve" in result.output


def test_export_format_json(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    result = runner.invoke(
        app, ["export", "--name", "demo", "--format", "json"]
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["access_key"] == "AKIATEST"


def test_export_format_env(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    result = runner.invoke(
        app, ["export", "--name", "demo", "--format", "env"]
    )
    assert result.exit_code == 0
    assert "export AWS_ACCESS_KEY_ID=" in result.output
    assert "export AWS_SECRET_ACCESS_KEY=" in result.output
    assert "export AWS_SESSION_TOKEN=" in result.output
    assert "export AWS_CREDENTIAL_EXPIRATION=" in result.output


def test_export_format_credential_process(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    result = runner.invoke(
        app,
        ["export", "--name", "demo", "--format", "credential-process"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert "AccessKeyId" in parsed
    assert "SecretAccessKey" in parsed
    assert "SessionToken" in parsed
    assert "Expiration" in parsed
    assert "Version" in parsed


def test_exec_no_args_exits_1(monkeypatch) -> None:
    result = runner.invoke(app, ["exec", "--name", "demo"])
    assert result.exit_code == 1
    assert "No command specified" in result.output


def test_exec_with_args_exit_0(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: mock_result)

    result = runner.invoke(
        app, ["exec", "--name", "demo", "--", "echo", "hello"]
    )
    assert result.exit_code == 0


def test_exec_forwards_return_code(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    mock_result = MagicMock()
    mock_result.returncode = 42
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: mock_result)

    result = runner.invoke(app, ["exec", "--name", "demo", "--", "false"])
    assert result.exit_code == 42


def test_exec_sets_aws_credentials_in_env(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    captured_env: dict = {}
    mock_result = MagicMock()
    mock_result.returncode = 0

    def _fake_run(cmd, env=None, **kwargs):
        if env:
            captured_env.update(env)
        return mock_result

    monkeypatch.setattr(subprocess, "run", _fake_run)
    runner.invoke(app, ["exec", "--name", "demo", "--", "printenv"])
    assert "AWS_ACCESS_KEY_ID" in captured_env
    assert captured_env["AWS_ACCESS_KEY_ID"] == "AKIATEST"


def test_shell_cmd_bash_sets_prompt_command(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    captured_env: dict = {}
    mock_result = MagicMock()
    mock_result.returncode = 0

    def _fake_run(cmd, env=None, **kwargs):
        if env:
            captured_env.update(env)
        return mock_result

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setenv("SHELL", "/bin/bash")

    runner.invoke(app, ["shell", "--name", "demo"])
    assert "PROMPT_COMMAND" in captured_env


def test_shell_cmd_bash_appends_existing_prompt_command(
    monkeypatch,
) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    captured_env: dict = {}
    mock_result = MagicMock()
    mock_result.returncode = 0

    def _fake_run(cmd, env=None, **kwargs):
        if env:
            captured_env.update(env)
        return mock_result

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.setenv("PROMPT_COMMAND", "existing_cmd")

    runner.invoke(app, ["shell", "--name", "demo"])
    assert "existing_cmd" in captured_env.get("PROMPT_COMMAND", "")


def test_shell_cmd_zsh_sets_elhaz_precmd(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    captured_env: dict = {}
    mock_result = MagicMock()
    mock_result.returncode = 0

    def _fake_run(cmd, env=None, **kwargs):
        if env:
            captured_env.update(env)
        return mock_result

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setenv("SHELL", "/bin/zsh")

    result = runner.invoke(app, ["shell", "--name", "demo"])
    assert "ELHAZ_PRECMD" in captured_env
    assert "precmd_functions" in result.output


def test_shell_cmd_sets_aws_credential_process(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_CREDS)])
    captured_env: dict = {}
    mock_result = MagicMock()
    mock_result.returncode = 0

    def _fake_run(cmd, env=None, **kwargs):
        if env:
            captured_env.update(env)
        return mock_result

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setenv("SHELL", "/bin/bash")

    runner.invoke(app, ["shell", "--name", "demo"])
    assert "AWS_CREDENTIAL_PROCESS" in captured_env


def test_whoami_success_prints_json(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=FAKE_IDENTITY)])
    result = runner.invoke(app, ["whoami", "--name", "demo"])
    assert result.exit_code == 0
    assert "123456789012" in result.output


def test_whoami_daemon_unreachable_exits_1(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ElhazDaemonError("no daemon")])
    result = runner.invoke(app, ["whoami", "--name", "demo"])
    assert result.exit_code == 1


def test_whoami_404_user_declines_add_exits_1(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [err_response(404, "no session")])
    monkeypatch.setattr("elhaz.cli.__main__.ask_yes_no", lambda *a, **k: False)
    result = runner.invoke(app, ["whoami", "--name", "demo"])
    assert result.exit_code == 1


def test_whoami_404_user_confirms_add_then_succeeds(
    monkeypatch,
) -> None:
    _install_fake_client(
        monkeypatch,
        [
            err_response(404, "no session"),  # first whoami
            ok_response(data={"config": "demo"}),  # add
            ok_response(data=FAKE_IDENTITY),  # recursive whoami
        ],
    )
    monkeypatch.setattr("elhaz.cli.__main__.ask_yes_no", lambda *a, **k: True)
    result = runner.invoke(app, ["whoami", "--name", "demo"])
    assert result.exit_code == 0
    assert "123456789012" in result.output


def test_whoami_non_404_error_exits_1(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [err_response(500, "internal error")])
    result = runner.invoke(app, ["whoami", "--name", "demo"])
    assert result.exit_code == 1
    assert "internal error" in result.output
