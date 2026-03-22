# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.cli.config subcommands."""

from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

import elhaz.cli.config as cli_config_module
from elhaz.cli.config import _open_in_editor, app
from elhaz.constants import Constants

runner = CliRunner()

ROLE_ARN = "arn:aws:iam::123456789012:role/TestRole"
MINIMAL_CONFIG = {"AssumeRole": {"RoleArn": ROLE_ARN}}


def _write_config(tmp_constants: Constants, name: str = "demo") -> None:
    """Create a valid YAML config file under tmp_constants.config_dir."""
    from elhaz.config import Config

    cfg = Config(name, tmp_constants)
    cfg.add(MINIMAL_CONFIG)


def _inject_state(monkeypatch, tmp_constants: Constants) -> None:
    """Inject tmp_constants as the ``state`` used by the config CLI module."""
    monkeypatch.setattr(cli_config_module, "state", tmp_constants)
    # prompts.list_local_configs and select_local_config also read state
    # indirectly via the constants arg passed by config module.
    # Since config.py passes `state` explicitly to list_local_configs/
    # select_local_config, patching cli_config_module.state is sufficient.


def test_config_list_no_configs(monkeypatch, tmp_constants: Constants) -> None:
    _inject_state(monkeypatch, tmp_constants)
    result = runner.invoke(app, ["list"])
    assert "No configs found." in result.output
    assert result.exit_code == 0


def test_config_list_with_configs(
    monkeypatch, tmp_constants: Constants
) -> None:
    _inject_state(monkeypatch, tmp_constants)
    _write_config(tmp_constants, "alpha")
    _write_config(tmp_constants, "beta")
    result = runner.invoke(app, ["list"])
    assert "alpha" in result.output
    assert "beta" in result.output
    assert result.exit_code == 0


def test_config_list_one_name_per_line(
    monkeypatch, tmp_constants: Constants
) -> None:
    _inject_state(monkeypatch, tmp_constants)
    _write_config(tmp_constants, "myconfig")
    result = runner.invoke(app, ["list"])
    lines = [l for l in result.output.splitlines() if l.strip()]  # noqa: E741
    assert "myconfig" in lines


def test_config_get_existing_prints_json(
    monkeypatch, tmp_constants: Constants
) -> None:
    _inject_state(monkeypatch, tmp_constants)
    _write_config(tmp_constants, "demo")
    result = runner.invoke(app, ["get", "--name", "demo"])
    assert result.exit_code == 0
    assert ROLE_ARN in result.output


def test_config_get_missing_file_user_declines_create(
    monkeypatch, tmp_constants: Constants
) -> None:
    _inject_state(monkeypatch, tmp_constants)
    monkeypatch.setattr(cli_config_module, "ask_yes_no", lambda *a, **k: False)
    result = runner.invoke(app, ["get", "--name", "missing"])
    assert result.exit_code == 0


def test_config_get_invalid_yaml_exits_1(
    monkeypatch, tmp_constants: Constants
) -> None:
    _inject_state(monkeypatch, tmp_constants)
    tmp_constants.config_dir.mkdir(parents=True, exist_ok=True)
    bad_file = tmp_constants.config_dir / "badconfig.yaml"
    # Write a YAML file that is structurally valid YAML but fails ConfigModel
    # validation (RoleArn is null → Pydantic rejects it).
    bad_file.write_text("AssumeRole:\n  RoleArn: null\n", encoding="utf-8")
    result = runner.invoke(app, ["get", "--name", "badconfig"])
    assert result.exit_code == 1


def test_config_remove_missing_file_exits_1(
    monkeypatch, tmp_constants: Constants
) -> None:
    _inject_state(monkeypatch, tmp_constants)
    result = runner.invoke(app, ["remove", "--name", "nothere"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


def test_config_remove_user_declines_exits_0(
    monkeypatch, tmp_constants: Constants
) -> None:
    _inject_state(monkeypatch, tmp_constants)
    _write_config(tmp_constants, "demo")
    monkeypatch.setattr(cli_config_module, "ask_yes_no", lambda *a, **k: False)
    result = runner.invoke(app, ["remove", "--name", "demo"])
    assert result.exit_code == 0


def test_config_remove_user_confirms_deletes_file(
    monkeypatch, tmp_constants: Constants
) -> None:
    _inject_state(monkeypatch, tmp_constants)
    _write_config(tmp_constants, "demo")
    file_path = tmp_constants.config_dir / "demo.yaml"
    assert file_path.exists()

    monkeypatch.setattr(cli_config_module, "ask_yes_no", lambda *a, **k: True)
    result = runner.invoke(app, ["remove", "--name", "demo"])
    assert result.exit_code == 0
    assert not file_path.exists()
    assert "demo" in result.output and "removed" in result.output.lower()


def test_open_in_editor_uses_editor_env(monkeypatch, tmp_path: Path) -> None:
    called_with: list = []

    def _fake_run(cmd, check=False, **kwargs):
        called_with.append(cmd)

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setenv("EDITOR", "nano")

    test_file = tmp_path / "demo.yaml"
    test_file.touch()
    _open_in_editor(test_file)

    assert len(called_with) == 1
    assert called_with[0][0] == "nano"
    assert str(test_file) in called_with[0]


def test_open_in_editor_defaults_to_vi(monkeypatch, tmp_path: Path) -> None:
    called_with: list = []

    def _fake_run(cmd, check=False, **kwargs):
        called_with.append(cmd)

    monkeypatch.setattr(subprocess, "run", _fake_run)
    # Ensure EDITOR is not set
    monkeypatch.delenv("EDITOR", raising=False)

    test_file = tmp_path / "demo.yaml"
    test_file.touch()
    _open_in_editor(test_file)

    assert len(called_with) == 1
    assert called_with[0][0] == "vi"
