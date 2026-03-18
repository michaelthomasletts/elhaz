import json
import socket
import threading
import time
import uuid
from pathlib import Path

from assume.constants import Constants
from assume.daemon import Client, Server


class FakeSTSClient:
    def get_caller_identity(self):
        return {
            "Account": "123456789012",
            "Arn": "arn:aws:sts::123456789012:assumed-role/demo/session",
            "UserId": "AROATEST:session",
        }


class FakeRefreshableSession:
    credentials = {
        "access_key": "access-key",
        "secret_key": "secret-key",
        "token": "token",
        "expiry_time": "2030-01-01T00:00:00Z",
    }

    def client(self, service_name: str):
        assert service_name == "sts"
        return FakeSTSClient()


class FakeSession:
    def __init__(self, name: str) -> None:
        self.name = name
        self.session = FakeRefreshableSession()


def _wait_for_socket(path, timeout: float = 2.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise AssertionError(f"Socket {path} was not created in time.")


def _socket_path(prefix: str) -> Path:
    return Path("/tmp") / f"{prefix}-{uuid.uuid4().hex}.sock"


def test_server_handles_multiple_client_connections(monkeypatch):
    monkeypatch.setattr("assume.daemon.Session", FakeSession)

    constants = Constants()
    constants.socket_path = _socket_path("assume-daemon-test")
    constants.max_unix_socket_connections = 2

    server = Server(constants)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    _wait_for_socket(constants.socket_path)

    first_client = Client(constants)
    first_response = json.loads(
        first_client.send({"action": "add", "config": "demo"})
    )
    first_client.close()

    second_client = Client(constants)
    second_response = json.loads(second_client.send({"action": "list"}))
    credentials_response = json.loads(
        second_client.send({"action": "credentials", "config": "demo"})
    )
    whoami_response = json.loads(
        second_client.send({"action": "whoami", "config": "demo"})
    )
    second_client.close()

    server.kill()
    server_thread.join(timeout=2)

    assert first_response == {
        "ok": True,
        "data": {"action": "add", "config": "demo"},
    }
    assert second_response == {"ok": True, "data": ["demo"]}
    assert credentials_response["ok"] is True
    assert credentials_response["data"]["access_key"] == "access-key"
    assert whoami_response == {
        "ok": True,
        "data": {
            "Account": "123456789012",
            "Arn": "arn:aws:sts::123456789012:assumed-role/demo/session",
            "UserId": "AROATEST:session",
        },
    }
    assert not server_thread.is_alive()


def test_server_returns_request_errors_without_exiting(monkeypatch):
    monkeypatch.setattr("assume.daemon.Session", FakeSession)

    constants = Constants()
    constants.socket_path = _socket_path("assume-daemon-test")

    server = Server(constants)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    _wait_for_socket(constants.socket_path)

    invalid_client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    invalid_client.connect(str(constants.socket_path))
    invalid_file = invalid_client.makefile("rwb")
    invalid_file.write(b"not-json\n")
    invalid_file.flush()
    invalid_response = json.loads(invalid_file.readline().decode("utf-8"))
    invalid_file.close()
    invalid_client.close()

    valid_client = Client(constants)
    valid_response = json.loads(valid_client.send({"action": "list"}))
    valid_client.close()

    server.kill()
    server_thread.join(timeout=2)

    assert invalid_response == {
        "ok": False,
        "error": "Invalid request: not-json",
    }
    assert valid_response == {"ok": True, "data": []}
    assert not server_thread.is_alive()
