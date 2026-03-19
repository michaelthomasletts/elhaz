import json
import os
import signal
import socket
import threading
import time
import uuid
from pathlib import Path

import pytest

from elhaz.constants import Constants
from elhaz.daemon import Client, DaemonService, Server
from elhaz.exceptions import ElhazDaemonError
from elhaz.models import ResponseModel


class FakeSTSClient:
    def get_caller_identity(self) -> dict:
        return {
            "Account": "123456789012",
            "Arn": ("arn:aws:sts::123456789012:assumed-role/demo/session"),
            "UserId": "AROATEST:session",
        }


class FakeRefreshableSession:
    credentials = {
        "access_key": "AKIATEST",
        "secret_key": "secret",
        "token": "token",
        "expiry_time": "2030-01-01T00:00:00Z",
    }

    def client(self, service_name: str) -> FakeSTSClient:
        return FakeSTSClient()


class FakeSession:
    def __init__(self, name: str) -> None:
        self.name = name
        self.session = FakeRefreshableSession()


def _socket_path(prefix: str = "elhaz-test") -> Path:
    return Path("/tmp") / f"{prefix}-{uuid.uuid4().hex}.sock"


def _wait_for_socket(path: Path, timeout: float = 2.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise AssertionError(f"Socket {path!r} did not appear in time.")


@pytest.fixture()
def constants() -> Constants:
    c = Constants()
    c.socket_path = _socket_path()
    return c


@pytest.fixture()
def service(monkeypatch) -> DaemonService:
    monkeypatch.setattr("elhaz.daemon.Session", FakeSession)
    return DaemonService()


@pytest.fixture()
def running_server(constants, service):
    server = Server(constants, service)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for_socket(constants.socket_path)
    yield server, constants
    server.stop()
    thread.join(timeout=2)


def test_add_session(running_server):
    server, constants = running_server
    with Client(constants) as client:
        response = client.send("add", {"config": "demo"})
    assert response.ok is True
    assert response.data == {"config": "demo"}
    assert response.error is None


def test_list_sessions(running_server):
    server, constants = running_server
    with Client(constants) as client:
        client.send("add", {"config": "demo"})
    with Client(constants) as client:
        response = client.send("list")
    assert response.ok is True
    assert response.data == ["demo"]
    assert response.version == 1


def test_credentials(running_server):
    server, constants = running_server
    with Client(constants) as client:
        client.send("add", {"config": "demo"})
    with Client(constants) as client:
        response = client.send("credentials", {"config": "demo"})
    assert response.ok is True
    assert response.data["access_key"] == "AKIATEST"
    assert response.data["secret_key"] == "secret"


def test_whoami(running_server):
    server, constants = running_server
    with Client(constants) as client:
        client.send("add", {"config": "demo"})
    with Client(constants) as client:
        response = client.send("whoami", {"config": "demo"})
    assert response.ok is True
    assert response.data == {
        "Account": "123456789012",
        "Arn": "arn:aws:sts::123456789012:assumed-role/demo/session",
        "UserId": "AROATEST:session",
    }


def test_remove_session(running_server):
    server, constants = running_server
    with Client(constants) as client:
        client.send("add", {"config": "demo"})
    with Client(constants) as client:
        response = client.send("remove", {"config": "demo"})
    assert response.ok is True
    assert response.data == {"config": "demo"}
    with Client(constants) as client:
        list_response = client.send("list")
    assert list_response.data == []


def test_request_id_is_echoed(running_server):
    """The response request_id must match the one sent in the request."""
    server, constants = running_server
    req_id = str(uuid.uuid4())

    raw_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    raw_sock.connect(str(constants.socket_path))
    conn_file = raw_sock.makefile("rwb")

    request = {
        "version": 1,
        "request_id": req_id,
        "action": "list",
        "payload": {},
    }
    conn_file.write(json.dumps(request).encode("utf-8") + b"\n")
    conn_file.flush()

    raw = conn_file.readline()
    conn_file.close()
    raw_sock.close()

    response = ResponseModel.model_validate_json(raw.rstrip())
    assert str(response.request_id) == req_id


def test_invalid_json_returns_structured_400(running_server):
    server, constants = running_server

    raw_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    raw_sock.connect(str(constants.socket_path))
    conn_file = raw_sock.makefile("rwb")
    conn_file.write(b"not-json\n")
    conn_file.flush()

    raw = conn_file.readline()
    conn_file.close()
    raw_sock.close()

    response = ResponseModel.model_validate_json(raw.rstrip())
    assert response.ok is False
    assert response.error is not None
    assert response.error.code == 400


def test_invalid_action_returns_400(running_server):
    """An action not in the Literal fails Pydantic validation -> 400."""
    server, constants = running_server

    raw_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    raw_sock.connect(str(constants.socket_path))
    conn_file = raw_sock.makefile("rwb")

    request = {
        "version": 1,
        "request_id": str(uuid.uuid4()),
        "action": "explode",
        "payload": {},
    }
    conn_file.write(json.dumps(request).encode("utf-8") + b"\n")
    conn_file.flush()

    raw = conn_file.readline()
    conn_file.close()
    raw_sock.close()

    response = ResponseModel.model_validate_json(raw.rstrip())
    assert response.ok is False
    assert response.error.code == 400


def test_missing_payload_config_returns_400(running_server):
    server, constants = running_server
    with Client(constants) as client:
        response = client.send("add", {})
    assert response.ok is False
    assert response.error.code == 400


def test_not_found_returns_404(running_server):
    server, constants = running_server
    with Client(constants) as client:
        response = client.send("credentials", {"config": "ghost"})
    assert response.ok is False
    assert response.error.code == 404


def test_remove_not_found_returns_404(running_server):
    server, constants = running_server
    with Client(constants) as client:
        response = client.send("remove", {"config": "ghost"})
    assert response.ok is False
    assert response.error.code == 404


def test_server_continues_after_error(running_server):
    """A failed request must not affect subsequent clients."""
    server, constants = running_server
    with Client(constants) as client:
        error_response = client.send("credentials", {"config": "ghost"})
    with Client(constants) as client:
        ok_response = client.send("list")
    assert error_response.ok is False
    assert ok_response.ok is True


def test_idle_client_does_not_block_second_client(running_server):
    """An open but idle connection must not block a second client."""
    server, constants = running_server

    idle = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    idle.connect(str(constants.socket_path))

    result: dict[str, ResponseModel] = {}

    def _send_list() -> None:
        with Client(constants) as client:
            result["response"] = client.send("list")

    t = threading.Thread(target=_send_list)
    t.start()
    t.join(timeout=2)
    idle.close()

    assert not t.is_alive(), "Second client thread timed out"
    assert result["response"].ok is True
    assert result["response"].data == []


def test_stop_removes_socket_file(constants, service):
    server = Server(constants, service)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for_socket(constants.socket_path)

    server.stop()
    thread.join(timeout=2)

    assert not constants.socket_path.exists()
    assert not thread.is_alive()


def test_stop_is_idempotent(constants, service):
    server = Server(constants, service)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for_socket(constants.socket_path)

    server.stop()
    server.stop()  # must not raise
    thread.join(timeout=2)

    assert not thread.is_alive()


def test_kill_stops_server(running_server):
    """kill action must shut the server down cleanly."""
    server, constants = running_server

    with Client(constants) as client:
        response = client.send("kill")

    assert response.ok is True

    # Socket file is removed once stop() completes.
    deadline = time.time() + 2.0
    while time.time() < deadline:
        if not constants.socket_path.exists():
            break
        time.sleep(0.01)
    assert not constants.socket_path.exists()


def test_startup_rejects_live_daemon(constants, service):
    """Server.__init__ must raise if a daemon is already listening."""
    server = Server(constants, service)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for_socket(constants.socket_path)

    try:
        with pytest.raises(ElhazDaemonError, match="already running"):
            Server(constants, DaemonService())
    finally:
        server.stop()
        thread.join(timeout=2)


def test_startup_clears_stale_socket(constants, service):
    """Server.__init__ must remove a dead socket file and start cleanly."""
    # Bind to the path and close without unlinking — leaves a stale file.
    stale = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    stale.bind(str(constants.socket_path))
    stale.close()

    assert constants.socket_path.exists()

    server = Server(constants, service)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for_socket(constants.socket_path)
    server.stop()
    thread.join(timeout=2)

    assert not thread.is_alive()


def test_startup_rejects_non_socket_path(constants, service):
    """Server.__init__ must raise if the path is a regular file."""
    constants.socket_path.write_bytes(b"")

    try:
        with pytest.raises(ElhazDaemonError, match="non-socket"):
            Server(constants, service)
    finally:
        constants.socket_path.unlink(missing_ok=True)


def test_client_wraps_connection_error(constants):
    """Client.__init__ must raise ElhazDaemonError when no daemon listens."""
    with pytest.raises(ElhazDaemonError, match="Could not connect"):
        Client(constants)


def test_stop_before_run_does_not_raise(constants, service):
    """stop() must be safe to call before run() is ever invoked.

    Exercises the self._sock None-guard and atexit-registered stop().
    """
    server = Server(constants, service)
    server.stop()  # must not raise
    assert not constants.socket_path.exists()


def test_signal_handlers_unchanged_from_non_main_thread(constants, service):
    """Signal handlers must not be modified when run() runs in a thread.

    All other tests call run() from a daemon thread, so this verifies
    the threading.main_thread() guard is in place.
    """
    before_sigterm = signal.getsignal(signal.SIGTERM)
    before_sigint = signal.getsignal(signal.SIGINT)

    server = Server(constants, service)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for_socket(constants.socket_path)
    server.stop()
    thread.join(timeout=2)

    assert signal.getsignal(signal.SIGTERM) is before_sigterm
    assert signal.getsignal(signal.SIGINT) is before_sigint


def test_sigterm_shuts_down_server(constants, service):
    """SIGTERM triggers clean shutdown when run() is called from main thread.

    Delivers SIGTERM to the current process from a timer thread. The
    signal is received in the main thread (where run() is blocked) and
    the registered handler calls stop(), causing the accept loop to exit.
    Original signal handlers are restored before this test returns.
    """
    server = Server(constants, service)

    # Fire SIGTERM after the server is listening. The 0.5 s accept()
    # timeout means run() exits within ~0.7 s of the signal.
    timer = threading.Timer(0.2, lambda: os.kill(os.getpid(), signal.SIGTERM))
    timer.start()
    try:
        server.run()  # blocks in the main thread
    finally:
        timer.cancel()

    assert not constants.socket_path.exists()
