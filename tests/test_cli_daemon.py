# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.cli.daemon subcommands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from typer.testing import CliRunner

import elhaz.cli.daemon as daemon_module
from elhaz.cli.daemon import (
    _daemon_subprocess_cmd,
    _is_running,
    _wait_until_running,
    _wait_until_stopped,
    app,
)
from elhaz.exceptions import ElhazDaemonError
from tests.conftest import err_response, ok_response

runner = CliRunner()


def _install_fake_client(monkeypatch, responses: list) -> None:
    """Patch elhaz.cli.daemon.Client with a fake using *responses*."""
    import collections

    queue: collections.deque = collections.deque(responses)

    class _FakeClient:
        def __init__(self, constants: Any) -> None:
            if queue and isinstance(queue[0], Exception):
                raise queue.popleft()

        def send(self, action: str, payload: dict | None = None) -> Any:
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

    monkeypatch.setattr(daemon_module, "Client", _FakeClient)


def test_is_running_returns_true_when_daemon_responds(
    monkeypatch,
) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=[])])
    assert _is_running() is True


def test_is_running_returns_false_on_daemon_error(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ElhazDaemonError("no daemon")])
    assert _is_running() is False


# ---------------------------------------------------------------------------
# _wait_until_running()
# ---------------------------------------------------------------------------


def test_wait_until_running_returns_true_immediately(
    monkeypatch,
) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: True)
    monkeypatch.setattr("time.sleep", lambda _: None)
    assert _wait_until_running(timeout=1.0) is True


def test_wait_until_running_returns_false_after_timeout(
    monkeypatch,
) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: False)
    monkeypatch.setattr("time.sleep", lambda _: None)
    assert _wait_until_running(timeout=0.0) is False


def test_wait_until_stopped_returns_true_immediately(
    monkeypatch,
) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: False)
    monkeypatch.setattr("time.sleep", lambda _: None)
    assert _wait_until_stopped(timeout=1.0) is True


def test_wait_until_stopped_returns_false_after_timeout(
    monkeypatch,
) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: True)
    monkeypatch.setattr("time.sleep", lambda _: None)
    assert _wait_until_stopped(timeout=0.0) is False


def test_daemon_subprocess_cmd_contains_executable() -> None:
    cmd = _daemon_subprocess_cmd()
    assert sys.executable in cmd


def test_daemon_subprocess_cmd_contains_module_flag() -> None:
    cmd = _daemon_subprocess_cmd()
    assert "-m" in cmd
    idx = cmd.index("-m")
    assert cmd[idx + 1] == "elhaz.cli"


def test_daemon_subprocess_cmd_contains_daemon_serve() -> None:
    cmd = _daemon_subprocess_cmd()
    assert "daemon" in cmd
    assert "_serve" in cmd


def test_daemon_subprocess_cmd_contains_socket_path() -> None:
    from elhaz import constants as _const

    cmd = _daemon_subprocess_cmd()
    assert "--socket-path" in cmd
    idx = cmd.index("--socket-path")
    assert cmd[idx + 1] == str(_const.state.socket_path)


def test_daemon_subprocess_cmd_contains_config_dir() -> None:
    from elhaz import constants as _const

    cmd = _daemon_subprocess_cmd()
    assert "--config-dir" in cmd
    idx = cmd.index("--config-dir")
    assert cmd[idx + 1] == str(_const.state.config_dir)


def test_daemon_subprocess_cmd_contains_max_cache_size() -> None:
    from elhaz import constants as _const

    cmd = _daemon_subprocess_cmd()
    assert "--max-daemon-cache-size" in cmd
    idx = cmd.index("--max-daemon-cache-size")
    assert cmd[idx + 1] == str(_const.state.max_daemon_cache_size)


def test_daemon_status_running(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: True)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "running" in result.output.lower()


def test_daemon_status_running_shows_socket_path(monkeypatch) -> None:
    from elhaz import constants as _const

    monkeypatch.setattr(daemon_module, "_is_running", lambda: True)
    result = runner.invoke(app, ["status"])
    assert str(_const.state.socket_path) in result.output


def test_daemon_status_not_running_exits_1(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: False)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "not running" in result.output.lower()


def test_daemon_start_already_running(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: True)
    result = runner.invoke(app, ["start"])
    assert "already running" in result.output
    assert result.exit_code == 0


def test_daemon_start_success(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: False)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: MagicMock())
    monkeypatch.setattr(
        daemon_module, "_wait_until_running", lambda timeout=5.0: True
    )
    result = runner.invoke(app, ["start"])
    assert "Daemon started" in result.output
    assert result.exit_code == 0


def test_daemon_start_times_out_exits_1(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: False)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: MagicMock())
    monkeypatch.setattr(
        daemon_module, "_wait_until_running", lambda timeout=5.0: False
    )
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 1
    assert "did not start" in result.output


def test_daemon_stop_not_running(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: False)
    result = runner.invoke(app, ["stop"])
    assert "not running" in result.output
    assert result.exit_code == 0


def test_daemon_stop_success(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: True)
    _install_fake_client(monkeypatch, [ok_response()])
    monkeypatch.setattr(
        daemon_module, "_wait_until_stopped", lambda timeout=5.0: True
    )
    result = runner.invoke(app, ["stop"])
    assert "Daemon stopped" in result.output
    assert result.exit_code == 0


def test_daemon_stop_kill_response_not_ok_exits_1(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: True)
    _install_fake_client(monkeypatch, [err_response(500, "kill failed")])
    result = runner.invoke(app, ["stop"])
    assert result.exit_code == 1


def test_daemon_stop_daemon_never_stops_exits_1(monkeypatch) -> None:
    monkeypatch.setattr(daemon_module, "_is_running", lambda: True)
    _install_fake_client(monkeypatch, [ok_response()])
    monkeypatch.setattr(
        daemon_module, "_wait_until_stopped", lambda timeout=5.0: False
    )
    result = runner.invoke(app, ["stop"])
    assert result.exit_code == 1
    assert "did not stop" in result.output


def test_daemon_logs_no_log_file(monkeypatch, tmp_path: Path) -> None:
    from elhaz import constants as _const

    _const.state.daemon_logging_path = tmp_path / "notexist.log"
    result = runner.invoke(app, ["logs"])
    assert "No log file found." in result.output


def test_daemon_logs_tail_default(monkeypatch, tmp_path: Path) -> None:
    from elhaz import constants as _const

    log_file = tmp_path / "daemon.log"
    lines = [f"line {i}\n" for i in range(100)]
    log_file.write_text("".join(lines), encoding="utf-8")
    _const.state.daemon_logging_path = log_file

    result = runner.invoke(app, ["logs"])
    assert result.exit_code == 0
    output_lines = [l for l in result.output.splitlines() if l.strip()]  # noqa: E741
    # default tail is 50; expect the last 50 lines
    assert len(output_lines) == 50
    # last line should be line 99
    assert "line 99" in output_lines[-1]


def test_daemon_logs_head_3(monkeypatch, tmp_path: Path) -> None:
    from elhaz import constants as _const

    log_file = tmp_path / "daemon.log"
    lines = [f"line {i}\n" for i in range(20)]
    log_file.write_text("".join(lines), encoding="utf-8")
    _const.state.daemon_logging_path = log_file

    result = runner.invoke(app, ["logs", "--head", "3"])
    assert result.exit_code == 0
    output_lines = [l for l in result.output.splitlines() if l.strip()]  # noqa: E741
    assert len(output_lines) == 3
    assert "line 0" in output_lines[0]


def test_daemon_logs_tail_0_shows_all(monkeypatch, tmp_path: Path) -> None:
    from elhaz import constants as _const

    log_file = tmp_path / "daemon.log"
    lines = [f"line {i}\n" for i in range(10)]
    log_file.write_text("".join(lines), encoding="utf-8")
    _const.state.daemon_logging_path = log_file

    result = runner.invoke(app, ["logs", "--tail", "0"])
    assert result.exit_code == 0
    output_lines = [l for l in result.output.splitlines() if l.strip()]  # noqa: E741
    assert len(output_lines) == 10


def test_daemon_list_daemon_unreachable_exits_1(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ElhazDaemonError("no daemon")])
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 1
    assert "Daemon unreachable" in result.output


def test_daemon_list_empty(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=[])])
    result = runner.invoke(app, ["list"])
    assert "No active sessions." in result.output


def test_daemon_list_sessions_echoed(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ok_response(data=["alpha", "beta"])])
    result = runner.invoke(app, ["list"])
    assert "alpha" in result.output
    assert "beta" in result.output


def test_daemon_add_success(monkeypatch) -> None:
    _install_fake_client(
        monkeypatch,
        [ok_response(data={"config": "demo"})],
    )
    result = runner.invoke(app, ["add", "--name", "demo"])
    assert result.exit_code == 0
    assert "demo" in result.output


def test_daemon_add_daemon_unreachable_exits_1(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ElhazDaemonError("no daemon")])
    result = runner.invoke(app, ["add", "--name", "demo"])
    assert result.exit_code == 1


def test_daemon_add_error_response_exits_1(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [err_response(500, "add failed")])
    result = runner.invoke(app, ["add", "--name", "demo"])
    assert result.exit_code == 1


def test_daemon_remove_success(monkeypatch) -> None:
    _install_fake_client(
        monkeypatch,
        [ok_response(data={"config": "demo"})],
    )
    result = runner.invoke(app, ["remove", "--name", "demo"])
    assert result.exit_code == 0
    assert "demo" in result.output


def test_daemon_remove_daemon_unreachable_exits_1(monkeypatch) -> None:
    _install_fake_client(monkeypatch, [ElhazDaemonError("no daemon")])
    result = runner.invoke(app, ["remove", "--name", "demo"])
    assert result.exit_code == 1
