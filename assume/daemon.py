import json
import os
import socket
from typing import Any, BinaryIO, Dict

from .constants import Constants
from .exceptions import AssumeDaemonError, AssumeValidationError
from .models import RequestModel
from .session import Session, SessionCache


class Client:
    def __init__(self, constants: Constants) -> None:
        self.constants = constants
        self.client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.client.connect(str(self.constants.socket_path))
        self.client_file = self.client.makefile("rwb")

    def send(self, request: Dict[str, str]) -> str:
        self._send_message(self.client_file, request)
        response: bytes = self.client_file.readline()
        if not response:
            raise AssumeDaemonError(
                "Daemon closed the connection without sending a response."
            )
        return response.decode("utf-8").rstrip("\n")

    @staticmethod
    def _send_message(connection_file: BinaryIO, payload: Any) -> None:
        connection_file.write(json.dumps(payload).encode("utf-8") + b"\n")
        connection_file.flush()

    def close(self) -> None:
        self.client_file.close()
        self.client.close()


class Server:
    def __init__(self, constants: Constants, **kwargs) -> None:
        self.constants = constants
        self.max_unix_socket_connections = kwargs.pop(
            "max_unix_socket_connections",
            self.constants.max_unix_socket_connections,
        )
        if (
            not isinstance(self.max_unix_socket_connections, int)
            or self.max_unix_socket_connections < 1
        ):
            raise AssumeValidationError(
                "Invalid max Unix socket connections: "
                f"'{self.max_unix_socket_connections}'"
            )
        self.cache = SessionCache(**kwargs)
        self._running = False

        # remove the socket file if it already exists
        try:
            os.unlink(self.constants.socket_path)
        except OSError:
            if os.path.exists(self.constants.socket_path):
                raise AssumeDaemonError(
                    "Could not remove existing socket file: "
                    f"{self.constants.socket_path}"
                )

        # create the socket and listen for connections
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(str(self.constants.socket_path))
        self.server.settimeout(0.5)
        self.server.listen(self.max_unix_socket_connections)

    def add(self, config: str) -> Dict[str, str]:
        try:
            self.cache[config] = Session(config)
            return {"action": "add", "config": config}
        except Exception as e:
            raise AssumeDaemonError(
                f"Failed to add session for config: '{config}'"
            ) from e

    def credentials(self, config: str) -> bytes:
        if (session := self.cache.get(config)) is None:
            raise AssumeDaemonError(
                f"No session found for any config named '{config}'. "
                "You may need to initialize the session for that config first."
            )

        return json.dumps(session.session.credentials).encode("utf-8")

    @staticmethod
    def _send_message(connection_file: BinaryIO, payload: Any) -> None:
        connection_file.write(json.dumps(payload).encode("utf-8") + b"\n")
        connection_file.flush()

    def kill(self) -> None:
        self._running = False

        try:
            self.server.close()
        except OSError:
            ...

        try:
            os.unlink(self.constants.socket_path)
        except FileNotFoundError:
            ...

    def list(self) -> list[str]:
        try:
            return list(self.cache.keys())
        except Exception as e:
            raise AssumeDaemonError("Failed to list sessions") from e

    def remove(self, config: str) -> Dict[str, str]:
        try:
            del self.cache[config]
            return {"action": "remove", "config": config}
        except Exception as e:
            raise AssumeDaemonError(
                f"Failed to remove session for config: '{config}'"
            ) from e

    def _dispatch(self, request: Dict[str, str]) -> Any:
        match action := request.pop("action"):
            case "add":
                return self.add(**request)
            case "credentials":
                return json.loads(self.credentials(**request).decode("utf-8"))
            case "list":
                return self.list()
            case "remove":
                return self.remove(**request)
            case "whoami":
                return json.loads(self.whoami(**request).decode("utf-8"))
            case _:
                raise AssumeDaemonError(f"Unknown action: '{action}'")

    def _handle_client(self, connection: socket.socket) -> None:
        with connection:
            connection_file = connection.makefile("rwb")
            with connection_file:
                while self._running:
                    response: bytes = connection_file.readline()

                    if not response:
                        break

                    _response: str = response.decode("utf-8").rstrip("\n")

                    try:
                        request: Dict[str, str] = RequestModel.model_validate(
                            json.loads(_response)
                        ).model_dump(exclude_none=True)
                    except Exception:
                        self._send_message(
                            connection_file,
                            {
                                "ok": False,
                                "error": f"Invalid request: {_response}",
                            },
                        )
                        continue

                    try:
                        data = self._dispatch(request)
                    except Exception as e:
                        self._send_message(
                            connection_file,
                            {"ok": False, "error": str(e)},
                        )
                        continue

                    self._send_message(
                        connection_file,
                        {"ok": True, "data": data},
                    )

    def run(self) -> None:
        self._running = True
        try:
            while self._running:
                try:
                    connection, _ = self.server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._running:
                        raise
                    break

                self._handle_client(connection)
        finally:
            self.kill()

    def whoami(self, config: str) -> bytes:
        if (session := self.cache.get(config)) is None:
            raise AssumeDaemonError(
                f"No session found for any config named '{config}'. "
                "You may need to initialize the session for that config first."
            )

        sts_client = session.session.client("sts")
        return json.dumps(sts_client.get_caller_identity()).encode("utf-8")
