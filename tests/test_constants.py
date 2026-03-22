# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.constants.Constants."""

from __future__ import annotations

from pathlib import Path

import pytest

from elhaz.constants import Constants
from elhaz.exceptions import ElhazValidationError


def test_config_dir_accepts_valid_path(tmp_path: Path) -> None:
    c = Constants()
    c.config_dir = tmp_path / "configs"
    assert c.config_dir == tmp_path / "configs"


def test_config_dir_rejects_none() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.config_dir = None  # type: ignore[assignment]


def test_config_dir_rejects_empty_string() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.config_dir = ""  # type: ignore[assignment]


def test_config_dir_rejects_string_path() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.config_dir = "/tmp/configs"  # type: ignore[assignment]


def test_config_dir_round_trip(tmp_path: Path) -> None:
    c = Constants()
    new_path = tmp_path / "myconfigs"
    c.config_dir = new_path
    assert c.config_dir == new_path


def test_socket_path_accepts_valid_path(tmp_path: Path) -> None:
    c = Constants()
    c.socket_path = tmp_path / "daemon.sock"
    assert c.socket_path == tmp_path / "daemon.sock"


def test_socket_path_rejects_none() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.socket_path = None  # type: ignore[assignment]


def test_socket_path_rejects_empty_string() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.socket_path = ""  # type: ignore[assignment]


def test_socket_path_rejects_string() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.socket_path = "/tmp/daemon.sock"  # type: ignore[assignment]


def test_socket_path_round_trip(tmp_path: Path) -> None:
    c = Constants()
    p = tmp_path / "sock" / "daemon.sock"
    c.socket_path = p
    assert c.socket_path == p


def test_daemon_logging_path_accepts_valid_path(tmp_path: Path) -> None:
    c = Constants()
    c.daemon_logging_path = tmp_path / "daemon.log"
    assert c.daemon_logging_path == tmp_path / "daemon.log"


def test_daemon_logging_path_rejects_none() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.daemon_logging_path = None  # type: ignore[assignment]


def test_daemon_logging_path_rejects_empty_string() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.daemon_logging_path = ""  # type: ignore[assignment]


def test_daemon_logging_path_rejects_string() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.daemon_logging_path = "/tmp/daemon.log"  # type: ignore[assignment]


def test_daemon_logging_path_round_trip(tmp_path: Path) -> None:
    c = Constants()
    p = tmp_path / "logs" / "daemon.log"
    c.daemon_logging_path = p
    assert c.daemon_logging_path == p


def test_max_unix_socket_connections_accepts_one() -> None:
    c = Constants()
    c.max_unix_socket_connections = 1
    assert c.max_unix_socket_connections == 1


def test_max_unix_socket_connections_accepts_large_int() -> None:
    c = Constants()
    c.max_unix_socket_connections = 100
    assert c.max_unix_socket_connections == 100


def test_max_unix_socket_connections_rejects_zero() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.max_unix_socket_connections = 0


def test_max_unix_socket_connections_rejects_negative() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.max_unix_socket_connections = -1


def test_max_unix_socket_connections_rejects_string() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.max_unix_socket_connections = "5"  # type: ignore[assignment]


def test_max_unix_socket_connections_round_trip() -> None:
    c = Constants()
    c.max_unix_socket_connections = 7
    assert c.max_unix_socket_connections == 7


def test_max_daemon_cache_size_accepts_one() -> None:
    c = Constants()
    c.max_daemon_cache_size = 1
    assert c.max_daemon_cache_size == 1


def test_max_daemon_cache_size_accepts_ten() -> None:
    c = Constants()
    c.max_daemon_cache_size = 10
    assert c.max_daemon_cache_size == 10


def test_max_daemon_cache_size_rejects_zero() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.max_daemon_cache_size = 0


def test_max_daemon_cache_size_rejects_negative() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.max_daemon_cache_size = -1


def test_max_daemon_cache_size_rejects_string() -> None:
    c = Constants()
    with pytest.raises(ElhazValidationError):
        c.max_daemon_cache_size = "10"  # type: ignore[assignment]


def test_max_daemon_cache_size_round_trip() -> None:
    c = Constants()
    c.max_daemon_cache_size = 3
    assert c.max_daemon_cache_size == 3


def test_config_file_extension_is_yaml() -> None:
    c = Constants()
    assert c.config_file_extension == ".yaml"


def test_config_file_extension_has_no_setter() -> None:
    c = Constants()
    with pytest.raises(AttributeError):
        c.config_file_extension = ".json"  # type: ignore[misc]


def test_multiple_instances_are_independent(tmp_path: Path) -> None:
    a = Constants()
    b = Constants()
    a.config_dir = tmp_path / "a_configs"
    assert b.config_dir != a.config_dir


def test_instance_defaults_unchanged_after_sibling_mutation(
    tmp_path: Path,
) -> None:
    a = Constants()
    b = Constants()
    default_dir = b.config_dir
    a.config_dir = tmp_path / "x"
    assert b.config_dir == default_dir
