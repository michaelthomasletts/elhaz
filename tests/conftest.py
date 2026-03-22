# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Shared fixtures and helpers for the elhaz test suite."""

from __future__ import annotations

import collections
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from elhaz.constants import Constants
from elhaz.models import ErrorModel, ResponseModel


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Save and restore the global state singleton between tests.

    Prevents test pollution from CLI invocations that mutate ``state``.
    """
    from elhaz import constants

    s = constants.state
    saved_config_dir = s.config_dir
    saved_socket_path = s.socket_path
    saved_logging_path = s.daemon_logging_path
    saved_max_connections = s.max_unix_socket_connections
    saved_max_cache = s.max_daemon_cache_size
    yield
    s.config_dir = saved_config_dir
    s.socket_path = saved_socket_path
    s.daemon_logging_path = saved_logging_path
    s.max_unix_socket_connections = saved_max_connections
    s.max_daemon_cache_size = saved_max_cache


class FakeSTSClient:
    """Minimal STS client stub."""

    def get_caller_identity(self) -> dict:
        return {
            "Account": "123456789012",
            "Arn": ("arn:aws:sts::123456789012:assumed-role/demo/session"),
            "UserId": "AROATEST:session",
            "ResponseMetadata": {"key": "val"},
        }


class FakeRefreshableSession:
    """Minimal STSRefreshableSession stub."""

    credentials: dict = {
        "access_key": "AKIATEST",
        "secret_key": "secret",
        "token": "token",
        "expiry_time": "2030-01-01T00:00:00Z",
    }

    def __init__(self, **kwargs: Any) -> None:
        pass

    def client(self, service_name: str) -> FakeSTSClient:
        return FakeSTSClient()


class FakeSession:
    """Minimal Session stub for DaemonService tests."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.session = FakeRefreshableSession()


class FakeConfig:
    """Minimal Config stub that returns an empty config dict."""

    def __init__(self, name: str, constants: Any = None) -> None:
        self._name = name

    @property
    def config(self) -> dict:
        return {}


class FakeSessionObj:
    """Minimal session object for SessionCache tests.

    Only carries the ``name`` attribute so SessionCache.__setitem__ can
    validate the key/name match without touching STSRefreshableSession.
    """

    def __init__(self, name: str) -> None:
        self.name = name


@pytest.fixture()
def tmp_constants(tmp_path: Path) -> Constants:
    """Return a Constants instance that writes under *tmp_path*.

    Parameters
    ----------
    tmp_path : Path
        pytest built-in temporary directory.

    Returns
    -------
    Constants
        Isolated constants object.
    """
    c = Constants()
    c.config_dir = tmp_path / "configs"
    c.socket_path = tmp_path / "daemon.sock"
    c.daemon_logging_path = tmp_path / "logs" / "daemon.log"
    return c


@pytest.fixture()
def minimal_config_dict() -> dict:
    """Return the smallest valid config payload."""
    return {
        "AssumeRole": {"RoleArn": "arn:aws:iam::123456789012:role/TestRole"}
    }


@pytest.fixture()
def written_config(tmp_constants: Constants, minimal_config_dict: dict):
    """Create a config file on disk and return its Config object.

    Parameters
    ----------
    tmp_constants : Constants
        Isolated constants with tmp_path-based config_dir.
    minimal_config_dict : dict
        Minimal valid config payload.

    Returns
    -------
    Config
        Config instance pointing at the written file.
    """
    from elhaz.config import Config

    cfg = Config("demo", tmp_constants)
    cfg.add(minimal_config_dict)
    return cfg


@pytest.fixture()
def clean_elhaz_logger():
    """Save and restore the ``elhaz`` logger handlers after the test.

    Not autouse — only requested by tests that call
    ``configure_daemon_logging``.
    """
    import logging

    pkg_logger = logging.getLogger("elhaz")
    saved_handlers = list(pkg_logger.handlers)
    saved_level = pkg_logger.level
    yield pkg_logger
    # remove any handlers added during the test
    for h in list(pkg_logger.handlers):
        pkg_logger.removeHandler(h)
        h.close()
    # restore originals
    for h in saved_handlers:
        pkg_logger.addHandler(h)
    pkg_logger.setLevel(saved_level)


def ok_response(data: Any = None) -> ResponseModel:
    """Return a successful ResponseModel with optional *data*.

    Parameters
    ----------
    data : Any, optional
        Payload to attach to the response.

    Returns
    -------
    ResponseModel
    """
    return ResponseModel(request_id=uuid4(), ok=True, data=data)


def err_response(code: int, message: str) -> ResponseModel:
    """Return an error ResponseModel.

    Parameters
    ----------
    code : int
        Numeric error code.
    message : str
        Human-readable error description.

    Returns
    -------
    ResponseModel
    """
    return ResponseModel(
        request_id=uuid4(),
        ok=False,
        error=ErrorModel(code=code, message=message),
    )


@pytest.fixture()
def make_fake_client():
    """Return a factory that installs a fake Client at a dotted attribute path.

    The factory signature is::

        install(module_attr_path: str, responses: list) -> None

    *responses* is a flat list of :class:`~elhaz.models.ResponseModel`
    instances consumed in order by ``send()``. If the **first** item in
    *responses* is an ``Exception`` instance it is raised from
    ``__init__`` (simulating a connection failure).

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Injected automatically by pytest.

    Returns
    -------
    callable
        The ``install`` factory.
    """
    import importlib

    def install(module_attr_path: str, responses: list) -> None:
        queue: collections.deque = collections.deque(responses)

        class _FakeClient:
            def __init__(self, constants: Any) -> None:
                if queue and isinstance(queue[0], Exception):
                    raise queue.popleft()

            def send(
                self, action: str, payload: dict | None = None
            ) -> ResponseModel:
                if not queue:
                    raise RuntimeError(
                        "FakeClient.send called but response queue is empty"
                    )
                item = queue.popleft()
                if isinstance(item, Exception):
                    raise item
                return item

            def close(self) -> None:
                pass

            def __enter__(self) -> "_FakeClient":
                return self

            def __exit__(self, *_: Any) -> None:
                self.close()

        # resolve the dotted path to (module, attribute)
        parts = module_attr_path.rsplit(".", 1)
        if len(parts) == 1:
            raise ValueError(
                f"module_attr_path must be dotted: {module_attr_path!r}"
            )
        mod_path, attr = parts
        mod = importlib.import_module(mod_path)
        setattr(mod, attr, _FakeClient)

    return install
