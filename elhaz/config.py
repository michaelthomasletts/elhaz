# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Read, validate, and transform persisted elhaz configs."""

__all__ = ["Config"]

import os
import re
from contextlib import contextmanager
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict, Generator

from boto3_refresh_session import AssumeRoleConfig, STSClientConfig
from ruamel.yaml import YAML

from .constants import Constants
from .exceptions import (
    ElhazAlreadyExistsError,
    ElhazNotFoundError,
    ElhazValidationError,
)
from .models import ConfigModel

# ruff: noqa: F401
match os.name:
    case "posix":
        import fcntl
    case "nt":
        import msvcrt


class Config:
    """Manage a single named config stored on disk.

    A :class:`Config` instance is responsible for validating the config name,
    locating the backing YAML file, coordinating file locking, and exposing
    helpers for CRUD-style operations and runtime transformation.

    Parameters
    ----------
    constants : Constants, optional
        An optional Constants instance for config file discovery. Default is a
        new Constants instance.
    name : str
        The name of the config to manage.

    Attributes
    ----------
    config : Dict[str, Any]
        A runtime-oriented view of the persisted config, suitable for
        downstream session setup.
    constants : Constants
        The Constants instance used for config file discovery.
    file_path : Path
        The absolute path to the config's YAML file.
    name : str
        The validated name of the config.

    Methods
    -------
    add(config: Dict[str, Any]) -> None
        Create a new config from validated input data.
    delete() -> None
        Delete the config file if it exists.
    edit(param: str, value: Any) -> None
        Replace a top-level config field and persist the result.
    get() -> Dict[str, Any]
        Load and validate a persisted config.
    lock(create=False, exist_ok=False) -> Generator[TextIOWrapper, None, None]
        Open the config file and hold an exclusive lock for the duration.
    rename(name: str) -> None
        Rename a config by copying it to a new validated file name.
    """

    def __init__(self, name: str, constants: Constants | None = None) -> None:
        self.name = name
        self.constants: Constants = constants or Constants()
        self.yaml: YAML = YAML(typ="rt")
        self.yaml.default_flow_style = False

    @property
    def name(self) -> str:
        """Return the validated config name."""

        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Sets the config name after validating it.

        Parameters
        ----------
        value : str
            The new name for the config.

        Raises
        ------
        ElhazValidationError
            If the new name is invalid.
        """

        if (
            not value
            or not isinstance(value, str)
            or not bool(re.compile(r"^[\w\-_]+$").match(value))
        ):
            raise ElhazValidationError(f"Invalid config name: '{value}'")

        self._name = value

    @property
    def file_path(self) -> Path:
        """Return the absolute path to this config's YAML file."""

        return self.constants.config_dir / (
            self.name + self.constants.config_file_extension
        )

    @staticmethod
    def _lock(obj) -> None:
        """Acquire an exclusive lock for an open config file handle."""

        match os.name:
            case "posix":
                fcntl.flock(obj.fileno(), fcntl.LOCK_EX)  # type: ignore
            case "nt":
                msvcrt.locking(obj.fileno(), msvcrt.LK_LOCK, 1)  # type: ignore

    @staticmethod
    def _unlock(obj) -> None:
        """Release a previously acquired lock for an open config file
        handle.
        """

        match os.name:
            case "posix":
                fcntl.flock(obj.fileno(), fcntl.LOCK_UN)  # type: ignore
            case "nt":
                msvcrt.locking(obj.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore

    @contextmanager
    def lock(
        self, *, create: bool = False, exist_ok: bool = False
    ) -> Generator[TextIOWrapper, None, None]:
        """Open the config file and hold an exclusive lock for the duration.

        The parent directory is created automatically when needed. The file
        itself is created only when ``create`` is ``True``. When the context
        exits, the file is flushed, synced to disk, and unlocked.

        Parameters
        ----------
        create : bool, optional
            Whether to create the config file if it does not already exist.
            Default is False.
        exist_ok : bool, optional
            Whether to allow the config file to already exist when locking. If
            False, an ElhazAlreadyExistsError will be raised if the config
            file already exists. Default is False.

        Raises
        ------
        ElhazAlreadyExistsError
            If exist_ok is False and the config file already exists.
        ElhazNotFoundError
            If create is False and the config file does not exist.

        Yields
        ------
        TextIOWrapper
            The opened config file in read/write text mode.
        """

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if self.file_path.exists():
            if not exist_ok:
                raise ElhazAlreadyExistsError(
                    message=f"Config '{self.name}' already exists",
                    param="name",
                    value=self.name,
                )
        elif create:
            self.file_path.touch()
        else:
            raise ElhazNotFoundError(
                message=f"Config '{self.name}' not found",
                param="name",
                value=self.name,
            )

        with open(self.file_path, "r+", encoding="utf-8") as f:
            self._lock(f)
            try:
                yield f
            finally:
                f.flush()
                os.fsync(f.fileno())
                self._unlock(f)

    def add(self, config: Dict[str, Any]) -> None:
        """Create a new config from validated input data.

        The supplied mapping is validated with :class:`ConfigModel` before it
        is serialized to YAML. Existing config files are not overwritten.

        Parameters
        ----------
        config : Dict[str, Any]
            The raw config payload to persist.

        Raises
        ------
        ElhazAlreadyExistsError
            If a config with the same name already exists.
        ElhazValidationError
            If the config is invalid.
        """

        with self.lock(create=True) as f:
            f.seek(0)

            try:
                self.yaml.dump(
                    ConfigModel(**config).model_dump(exclude_none=True), f
                )
            except Exception as err:
                raise ElhazValidationError(f"Invalid config: {err}")

            f.truncate()

    def get(self) -> Dict[str, Any]:
        """Load and validate a persisted config.

        Returns
        -------
        Dict[str, Any]
            The normalized config payload with ``None`` values removed.

        Raises
        ------
        ElhazNotFoundError
            If the config does not exist.
        ElhazValidationError
            If the config is invalid.
        """

        with self.lock(exist_ok=True) as f:
            try:
                return ConfigModel(**self.yaml.load(f) or {}).model_dump(
                    exclude_none=True
                )
            except Exception as err:
                raise ElhazValidationError(f"Invalid config: {err}")

    def edit(self, param: str, value: Any) -> None:
        """Replace a top-level config field and persist the result.

        The update is applied in-memory, validated as a complete
        :class:`ConfigModel`, and then written back to disk only if the full
        config remains valid.

        Parameters
        ----------
        param : str
            The top-level config key to replace.
        value : Any
            The new value for ``param``.

        Raises
        ------
        ElhazNotFoundError
            If the config does not exist.
        ElhazValidationError
            If the config is invalid after editing.
        """

        with self.lock(exist_ok=True) as f:
            config = self.yaml.load(f) or {}
            config[param] = value

            try:
                config = ConfigModel(**config).model_dump(exclude_none=True)
            except Exception as err:
                raise ElhazValidationError(f"Invalid config: {err}")

            f.seek(0)
            self.yaml.dump(config, f)
            f.truncate()

    def delete(self) -> None:
        """Delete the config file if it exists.

        Missing files are ignored.
        """

        self.file_path.unlink(missing_ok=True)

    def rename(self, name: str) -> None:
        """Rename a config by copying it to a new validated file name.

        The destination config is written before the source is deleted, so a
        failure while creating the new file does not remove the original. A
        rename to the current name is treated as a no-op.

        Parameters
        ----------
        name : str
            The new name for the config.

        Raises
        ------
        ElhazAlreadyExistsError
            If a config with the new name already exists.
        ElhazNotFoundError
            If the source config does not exist.
        ElhazValidationError
            If the new name is invalid or the source config is invalid.
        """

        target = Config(name)
        if target.file_path == self.file_path:
            return

        config = self.get()
        target.add(config)
        self.delete()
        self.name = target.name

    @property
    def config(self) -> Dict[str, Any]:
        """Return a runtime-oriented view of the persisted config.

        This starts with the required ``AssumeRole`` payload and then merges
        in any additional optional sections recognized by this method:

        - ``STS`` is attached under the ``"STS"`` key.
        - ``MFA`` provider settings are added if present.
        - ``Session`` values are merged into the top-level mapping if present.

        Returns
        -------
        Dict[str, Any]
            A transformed config mapping suitable for downstream session setup.

        Raises
        ------
        ElhazNotFoundError
            If the config does not exist.
        ElhazValidationError
            If the persisted config is invalid.
        """

        config = self.get()

        # AssumeRole is guaranteed to exist by get()
        transformed_config: Dict[str, Any] = {
            "assume_role_kwargs": AssumeRoleConfig(**config["AssumeRole"])
        }

        if sts := config.get("STS"):
            transformed_config["sts_client_kwargs"] = STSClientConfig(**sts)
        if cmd := config.get("MFA", {}).get("command"):
            transformed_config["mfa_token_provider"] = cmd
        if timeout := config.get("MFA", {}).get("timeout"):
            transformed_config["mfa_token_provider_kwargs"] = {
                "timeout": timeout
            }
        if session := config.get("Session"):
            transformed_config.update(**session)

        return transformed_config
