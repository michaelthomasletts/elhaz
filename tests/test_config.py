# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.config.Config."""

from __future__ import annotations

import pytest

from elhaz.config import Config
from elhaz.constants import Constants
from elhaz.exceptions import (
    ElhazAlreadyExistsError,
    ElhazNotFoundError,
    ElhazValidationError,
)

ROLE_ARN = "arn:aws:iam::123456789012:role/TestRole"
MINIMAL_CONFIG = {"AssumeRole": {"RoleArn": ROLE_ARN}}


@pytest.mark.parametrize(
    "bad_name",
    ["", "   ", " with space", "with/slash"],
)
def test_config_name_invalid_strings_raise(
    bad_name: str,
    tmp_constants: Constants,
) -> None:
    with pytest.raises(ElhazValidationError):
        Config(bad_name, tmp_constants)


def test_config_name_non_string_raises(tmp_constants: Constants) -> None:
    with pytest.raises(ElhazValidationError):
        Config(123, tmp_constants)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "good_name",
    ["demo", "my-config", "config_1", "abc123"],
)
def test_config_name_valid_strings_accepted(
    good_name: str,
    tmp_constants: Constants,
) -> None:
    cfg = Config(good_name, tmp_constants)
    assert cfg.name == good_name


def test_config_name_setter_updates_name(tmp_constants: Constants) -> None:
    cfg = Config("original", tmp_constants)
    cfg.name = "updated"
    assert cfg.name == "updated"


def test_file_path_combines_dir_name_and_extension(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    expected = tmp_constants.config_dir / "demo.yaml"
    assert cfg.file_path == expected


def test_lock_create_true_creates_file(tmp_constants: Constants) -> None:
    cfg = Config("demo", tmp_constants)
    with cfg.lock(create=True):
        pass
    assert cfg.file_path.exists()


def test_lock_create_false_absent_raises_not_found(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    with pytest.raises(ElhazNotFoundError):
        with cfg.lock(create=False):
            pass


def test_lock_exist_ok_false_present_raises_already_exists(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.file_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.file_path.touch()
    with pytest.raises(ElhazAlreadyExistsError):
        with cfg.lock(exist_ok=False):
            pass


def test_lock_exist_ok_true_present_yields_handle(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.file_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.file_path.touch()
    with cfg.lock(exist_ok=True) as fh:
        assert fh is not None


def test_lock_creates_parent_directory(tmp_constants: Constants) -> None:
    nested = tmp_constants.config_dir / "sub"
    tmp_constants.config_dir = nested
    cfg = Config("demo", tmp_constants)
    assert not nested.exists()
    with cfg.lock(create=True):
        pass
    assert nested.exists()


def test_add_creates_yaml_file(tmp_constants: Constants) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    assert cfg.file_path.exists()


def test_add_raises_already_exists_if_file_present(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    with pytest.raises(ElhazAlreadyExistsError):
        cfg.add(MINIMAL_CONFIG)


def test_add_raises_validation_error_for_missing_assume_role(
    tmp_constants: Constants,
) -> None:
    cfg = Config("bad", tmp_constants)
    with pytest.raises(ElhazValidationError):
        cfg.add({"NotAssumeRole": {}})


def test_add_content_round_trips_through_get(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    loaded = cfg.get()
    assert loaded["AssumeRole"]["RoleArn"] == ROLE_ARN


def test_get_returns_dict_with_assume_role(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    result = cfg.get()
    assert "AssumeRole" in result
    assert result["AssumeRole"]["RoleArn"] == ROLE_ARN


def test_get_raises_not_found_if_file_absent(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    with pytest.raises(ElhazNotFoundError):
        cfg.get()


def test_get_raises_validation_error_for_corrupt_yaml(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.file_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.file_path.write_text(
        "AssumeRole:\n  RoleArn: null\n", encoding="utf-8"
    )
    with pytest.raises(ElhazValidationError):
        cfg.get()


def test_edit_updates_existing_field(tmp_constants: Constants) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    new_arn = "arn:aws:iam::999999999999:role/Other"
    cfg.edit("AssumeRole", {"RoleArn": new_arn})
    result = cfg.get()
    assert result["AssumeRole"]["RoleArn"] == new_arn


def test_edit_adds_new_section(tmp_constants: Constants) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    cfg.edit("STS", {"region_name": "eu-west-1"})
    result = cfg.get()
    assert "STS" in result
    assert result["STS"]["region_name"] == "eu-west-1"


def test_edit_raises_not_found_if_file_absent(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    with pytest.raises(ElhazNotFoundError):
        cfg.edit("STS", {"region_name": "us-east-1"})


def test_delete_removes_file(tmp_constants: Constants) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    assert cfg.file_path.exists()
    cfg.delete()
    assert not cfg.file_path.exists()


def test_delete_missing_file_is_no_op(tmp_constants: Constants) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.delete()  # must not raise


def test_rename_self_is_no_op(tmp_constants: Constants) -> None:
    """Self-rename with a fresh Config that has matching file path is no-op.

    Config.rename() creates ``target = Config(name)`` without inheriting
    constants, so the no-op guard ``target.file_path == self.file_path``
    only fires when both sides resolve to the same absolute path — i.e.
    when the source Config also uses the default Constants.  We verify the
    guard separately using identical paths.
    """
    from unittest.mock import patch

    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    # Simulate same file path by patching Config to use tmp_constants too
    with patch("elhaz.config.Config") as MockConfig:
        mock_target = MockConfig.return_value
        mock_target.file_path = cfg.file_path  # same path → no-op guard
        cfg.rename("demo")
    # file should still be present (no-op path returned early)
    assert cfg.file_path.exists()
    assert cfg.name == "demo"


def test_rename_normal_creates_new_deletes_old(
    tmp_constants: Constants,
) -> None:
    """rename() writes to target (using a fresh Config with tmp_constants)."""
    from unittest.mock import patch

    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    old_path = cfg.file_path

    # Patch Config inside elhaz.config so target uses tmp_constants
    target_cfg = Config("renamed", tmp_constants)

    with patch("elhaz.config.Config", return_value=target_cfg) as MockConfig:
        MockConfig.side_effect = lambda name: Config(name, tmp_constants)
        cfg.rename("renamed")

    assert not old_path.exists()
    assert cfg.name == "renamed"
    assert target_cfg.file_path.exists()


def test_rename_raises_already_exists_if_target_exists(
    tmp_constants: Constants,
) -> None:
    """rename() raises if target already exists (using tmp_constants)."""
    from unittest.mock import patch

    cfg_a = Config("alpha", tmp_constants)
    cfg_a.add(MINIMAL_CONFIG)
    cfg_b = Config("beta", tmp_constants)
    cfg_b.add(MINIMAL_CONFIG)

    with patch("elhaz.config.Config") as MockConfig:
        MockConfig.side_effect = lambda name: Config(name, tmp_constants)
        with pytest.raises(ElhazAlreadyExistsError):
            cfg_a.rename("beta")


def test_rename_source_preserved_when_target_exists(
    tmp_constants: Constants,
) -> None:
    """rename() leaves source intact when target already exists."""
    from unittest.mock import patch

    cfg_a = Config("alpha", tmp_constants)
    cfg_a.add(MINIMAL_CONFIG)
    cfg_b = Config("beta", tmp_constants)
    cfg_b.add(MINIMAL_CONFIG)

    with patch("elhaz.config.Config") as MockConfig:
        MockConfig.side_effect = lambda name: Config(name, tmp_constants)
        try:
            cfg_a.rename("beta")
        except ElhazAlreadyExistsError:
            pass
    assert Config("alpha", tmp_constants).file_path.exists()


def test_config_property_minimal_has_assume_role_kwargs(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    result = cfg.config
    assert "assume_role_kwargs" in result


def test_config_property_minimal_has_no_sts_key(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(MINIMAL_CONFIG)
    result = cfg.config
    assert "sts_client_kwargs" not in result


def test_config_property_with_sts_section(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(
        {
            "AssumeRole": {"RoleArn": ROLE_ARN},
            "STS": {"region_name": "us-west-2"},
        }
    )
    result = cfg.config
    assert "sts_client_kwargs" in result


def test_config_property_with_mfa_section(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(
        {
            "AssumeRole": {"RoleArn": ROLE_ARN},
            "MFA": {"command": "oathtool", "timeout": 60},
        }
    )
    result = cfg.config
    assert "mfa_token_provider" in result
    assert "mfa_token_provider_kwargs" in result
    assert result["mfa_token_provider_kwargs"]["timeout"] == 60


def test_config_property_with_session_section(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(
        {
            "AssumeRole": {"RoleArn": ROLE_ARN},
            "Session": {"region_name": "ap-east-1"},
        }
    )
    result = cfg.config
    assert "region_name" in result
    assert result["region_name"] == "ap-east-1"


def test_config_property_combined_all_sections(
    tmp_constants: Constants,
) -> None:
    cfg = Config("demo", tmp_constants)
    cfg.add(
        {
            "AssumeRole": {"RoleArn": ROLE_ARN},
            "STS": {"region_name": "us-east-1"},
            "MFA": {"command": "token-cmd", "timeout": 30},
            "Session": {"region_name": "eu-west-1"},
        }
    )
    result = cfg.config
    assert "assume_role_kwargs" in result
    assert "sts_client_kwargs" in result
    assert "mfa_token_provider" in result
    assert "mfa_token_provider_kwargs" in result
    assert "region_name" in result
