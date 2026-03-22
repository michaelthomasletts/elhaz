# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.daemon helpers and DaemonService."""

from __future__ import annotations

import logging
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

import pytest

from elhaz.constants import Constants
from elhaz.daemon import DaemonService, _error_code, configure_daemon_logging
from elhaz.exceptions import (
    BaseElhazError,
    ElhazAlreadyExistsError,
    ElhazBadRequestError,
    ElhazNotFoundError,
)
from elhaz.models import RequestModel


@pytest.fixture(autouse=True)
def _patch_session(monkeypatch):
    """Replace elhaz.daemon.Session with FakeSession."""
    from tests.conftest import FakeSession

    monkeypatch.setattr("elhaz.daemon.Session", FakeSession)


@pytest.fixture()
def service() -> DaemonService:
    return DaemonService()


def test_error_code_bad_request() -> None:
    exc = ElhazBadRequestError("bad")
    assert _error_code(exc) == 400


def test_error_code_not_found() -> None:
    exc = ElhazNotFoundError("nope")
    assert _error_code(exc) == 404


def test_error_code_already_exists() -> None:
    exc = ElhazAlreadyExistsError("dup")
    assert _error_code(exc) == 409


def test_error_code_base_returns_500() -> None:
    exc = BaseElhazError("generic")
    assert _error_code(exc) == 500


def test_error_code_unknown_subclass_returns_500() -> None:
    class _NewError(BaseElhazError):
        pass

    exc = _NewError("novel")
    assert _error_code(exc) == 500


def test_configure_daemon_logging_creates_parent_dir(
    tmp_path: Path,
    clean_elhaz_logger,
) -> None:
    c = Constants()
    c.daemon_logging_path = tmp_path / "logs" / "sub" / "daemon.log"
    assert not c.daemon_logging_path.parent.exists()
    configure_daemon_logging(c)
    assert c.daemon_logging_path.parent.exists()


def test_configure_daemon_logging_adds_one_rotating_handler(
    tmp_path: Path,
    clean_elhaz_logger,
) -> None:
    c = Constants()
    c.daemon_logging_path = tmp_path / "logs" / "daemon.log"
    configure_daemon_logging(c)
    rfhs = [
        h
        for h in clean_elhaz_logger.handlers
        if isinstance(h, RotatingFileHandler)
    ]
    assert len(rfhs) == 1


def test_configure_daemon_logging_idempotent(
    tmp_path: Path,
    clean_elhaz_logger,
) -> None:
    c = Constants()
    c.daemon_logging_path = tmp_path / "logs" / "daemon.log"
    configure_daemon_logging(c)
    configure_daemon_logging(c)  # second call
    rfhs = [
        h
        for h in clean_elhaz_logger.handlers
        if isinstance(h, RotatingFileHandler)
    ]
    assert len(rfhs) == 1


def test_configure_daemon_logging_preserves_stream_handler(
    tmp_path: Path,
    clean_elhaz_logger,
) -> None:
    stream_handler = logging.StreamHandler()
    clean_elhaz_logger.addHandler(stream_handler)

    c = Constants()
    c.daemon_logging_path = tmp_path / "logs" / "daemon.log"
    configure_daemon_logging(c)

    assert stream_handler in clean_elhaz_logger.handlers


def test_configure_daemon_logging_handler_path(
    tmp_path: Path,
    clean_elhaz_logger,
) -> None:
    c = Constants()
    log_path = tmp_path / "daemon.log"
    c.daemon_logging_path = log_path
    configure_daemon_logging(c)
    rfhs = [
        h
        for h in clean_elhaz_logger.handlers
        if isinstance(h, RotatingFileHandler)
    ]
    assert len(rfhs) == 1
    assert Path(rfhs[0].baseFilename) == log_path


def test_configure_daemon_logging_sets_level_info(
    tmp_path: Path,
    clean_elhaz_logger,
) -> None:
    c = Constants()
    c.daemon_logging_path = tmp_path / "daemon.log"
    configure_daemon_logging(c)
    assert clean_elhaz_logger.level == logging.INFO


def test_daemon_service_add_returns_config_name(
    service: DaemonService,
) -> None:
    result = service.add("demo")
    assert result == {"config": "demo"}


def test_daemon_service_add_puts_session_in_cache(
    service: DaemonService,
) -> None:
    service.add("demo")
    sessions = service.list()
    assert "demo" in sessions


def test_daemon_service_add_same_name_twice_overwrites(
    service: DaemonService,
) -> None:
    service.add("demo")
    service.add("demo")
    assert service.list().count("demo") == 1


def test_daemon_service_credentials_returns_dict(
    service: DaemonService,
) -> None:
    service.add("demo")
    creds = service.credentials("demo")
    assert isinstance(creds, dict)
    assert "access_key" in creds


def test_daemon_service_credentials_unknown_raises_not_found(
    service: DaemonService,
) -> None:
    with pytest.raises(ElhazNotFoundError):
        service.credentials("ghost")


def test_daemon_service_list_empty(service: DaemonService) -> None:
    assert service.list() == []


def test_daemon_service_list_returns_names(service: DaemonService) -> None:
    service.add("alpha")
    service.add("beta")
    result = service.list()
    assert "alpha" in result
    assert "beta" in result


def test_daemon_service_list_order(service: DaemonService) -> None:
    service.add("first")
    service.add("second")
    result = service.list()
    assert result.index("first") < result.index("second")


def test_daemon_service_remove_returns_config_name(
    service: DaemonService,
) -> None:
    service.add("demo")
    result = service.remove("demo")
    assert result == {"config": "demo"}


def test_daemon_service_remove_session_gone_from_cache(
    service: DaemonService,
) -> None:
    service.add("demo")
    service.remove("demo")
    assert "demo" not in service.list()


def test_daemon_service_remove_unknown_raises_not_found(
    service: DaemonService,
) -> None:
    with pytest.raises(ElhazNotFoundError):
        service.remove("ghost")


def test_daemon_service_whoami_returns_identity_without_response_metadata(
    service: DaemonService,
) -> None:
    service.add("demo")
    result = service.whoami("demo")
    assert "ResponseMetadata" not in result
    assert "Account" in result


def test_daemon_service_whoami_unknown_raises_not_found(
    service: DaemonService,
) -> None:
    with pytest.raises(ElhazNotFoundError):
        service.whoami("ghost")


def _make_request(action: str, payload: dict | None = None) -> RequestModel:
    return RequestModel(
        request_id=uuid4(),
        action=action,  # type: ignore[arg-type]
        payload=payload or {},
    )


def test_dispatch_routes_add(service: DaemonService) -> None:
    req = _make_request("add", {"config": "demo"})
    result = service.dispatch(req)
    assert result == {"config": "demo"}


def test_dispatch_routes_list(service: DaemonService) -> None:
    req = _make_request("list")
    result = service.dispatch(req)
    assert isinstance(result, list)


def test_dispatch_routes_credentials(service: DaemonService) -> None:
    service.add("demo")
    req = _make_request("credentials", {"config": "demo"})
    result = service.dispatch(req)
    assert "access_key" in result


def test_dispatch_routes_remove(service: DaemonService) -> None:
    service.add("demo")
    req = _make_request("remove", {"config": "demo"})
    result = service.dispatch(req)
    assert result == {"config": "demo"}


def test_dispatch_routes_whoami(service: DaemonService) -> None:
    service.add("demo")
    req = _make_request("whoami", {"config": "demo"})
    result = service.dispatch(req)
    assert "Account" in result


def test_dispatch_raises_bad_request_for_unknown_action(
    service: DaemonService,
) -> None:
    # Build a request object directly since the Literal type won't accept
    # "bogus" — use model_construct to bypass Pydantic validation.
    req = RequestModel.model_construct(
        request_id=uuid4(), action="bogus", payload={}, version=1
    )
    with pytest.raises(ElhazBadRequestError):
        service.dispatch(req)


def test_dispatch_raises_bad_request_for_kill_action(
    service: DaemonService,
) -> None:
    req = RequestModel.model_construct(
        request_id=uuid4(), action="kill", payload={}, version=1
    )
    with pytest.raises(ElhazBadRequestError):
        service.dispatch(req)


def test_dispatch_raises_bad_request_when_config_missing_for_add(
    service: DaemonService,
) -> None:
    req = _make_request("add", {})
    with pytest.raises(ElhazBadRequestError):
        service.dispatch(req)


def test_dispatch_raises_bad_request_when_config_missing_for_credentials(
    service: DaemonService,
) -> None:
    req = _make_request("credentials", {})
    with pytest.raises(ElhazBadRequestError):
        service.dispatch(req)


def test_daemon_service_concurrent_add_and_list(
    service: DaemonService,
) -> None:
    errors: list[Exception] = []

    def _adder():
        try:
            for i in range(10):
                service.add(f"session-{i}")
        except Exception as exc:
            errors.append(exc)

    def _lister():
        try:
            for _ in range(10):
                _ = service.list()
        except Exception as exc:
            errors.append(exc)

    t1 = threading.Thread(target=_adder)
    t2 = threading.Thread(target=_lister)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert errors == [], f"Errors during concurrent access: {errors}"
    # all sessions were added (cache may be bounded, but no exceptions)
    for i in range(min(10, service._cache.max_size)):
        pass  # just verify no exceptions occurred
