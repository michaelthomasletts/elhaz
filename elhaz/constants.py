# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

__all__ = ["Constants"]

from pathlib import Path

from elhaz.exceptions import ElhazValidationError


class Constants:
    """Constants for config file discovery and management and daemon
    configuration.

    Attributes
    ----------
    config_dir : Path
        The directory where config files are stored. Default is
        ~/.elhaz/configs.
    config_file_extension : str
        The file extension for config files. Default is .yaml.
    socket_path : Path
        The path to the Unix socket for daemon communication. Default is
        ~/.elhaz/sock/daemon.sock.
    daemon_logging_path : Path
        The path to the log file for the daemon. Default is
        ~/.elhaz/logs/daemon.log.
    max_unix_socket_connections : int
        The maximum number of pending Unix socket connections the daemon will
        allow in its listen backlog. Default is 5.
    """

    _config_dir: Path = Path.home() / ".elhaz/configs"
    _config_file_extension: str = ".yaml"
    _socket_path: Path = Path.home() / ".elhaz" / "sock" / "daemon.sock"
    _daemon_logging_path: Path = Path.home() / ".elhaz/logs/daemon.log"
    _max_unix_socket_connections: int = 5

    @property
    def config_dir(self) -> Path:
        return self._config_dir

    @config_dir.setter
    def config_dir(self, value: Path) -> None:
        if not value or not isinstance(value, Path):
            raise ElhazValidationError(f"Invalid config directory: '{value}'")
        self._config_dir = value

    @property
    def config_file_extension(self) -> str:
        return self._config_file_extension

    @config_file_extension.setter
    def config_file_extension(self, value: str) -> None:
        if (
            not value
            or not isinstance(value, str)
            or not value.startswith(".")
        ):
            raise ElhazValidationError(
                f"Invalid config file extension: '{value}'"
            )
        self._config_file_extension = value

    @property
    def socket_path(self) -> Path:
        return self._socket_path

    @socket_path.setter
    def socket_path(self, value: Path) -> None:
        if not value or not isinstance(value, Path):
            raise ElhazValidationError(f"Invalid socket path: '{value}'")
        self._socket_path = value

    @property
    def max_unix_socket_connections(self) -> int:
        return self._max_unix_socket_connections

    @max_unix_socket_connections.setter
    def max_unix_socket_connections(self, value: int) -> None:
        if not isinstance(value, int) or value < 1:
            raise ElhazValidationError(
                f"Invalid max Unix socket connections: '{value}'"
            )
        self._max_unix_socket_connections = value

    @property
    def daemon_logging_path(self) -> Path:
        return self._daemon_logging_path

    @daemon_logging_path.setter
    def daemon_logging_path(self, value: Path) -> None:
        if not value or not isinstance(value, Path):
            raise ElhazValidationError(
                f"Invalid daemon logging path: '{value}'"
            )
        self._daemon_logging_path = value
