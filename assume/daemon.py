"""UNIX socket daemon for managing refreshable AWS sessions."""

__all__ = ["Client", "DaemonService", "Server"]

import logging
import os
import socket
import threading
from typing import Any, Dict
from uuid import uuid4

from .constants import Constants
from .exceptions import (
    AssumeAlreadyExistsError,
    AssumeBadRequestError,
    AssumeDaemonError,
    AssumeNotFoundError,
    BaseAssumeError,
)
from .models import ErrorModel, RequestModel, ResponseModel
from .session import Session, SessionCache

logger = logging.getLogger(__name__)

_ERROR_CODES: Dict[type[BaseAssumeError], int] = {
    AssumeBadRequestError: 400,
    AssumeNotFoundError: 404,
    AssumeAlreadyExistsError: 409,
}


def _error_code(exc: BaseAssumeError) -> int:
    """Return the integer error code for a BaseAssumeError subtype.

    Parameters
    ----------
    exc : BaseAssumeError
        The exception to map.

    Returns
    -------
    int
        400, 404, 409, or 500.
    """

    return _ERROR_CODES.get(type(exc), 500)


class DaemonService:
    """Business logic layer for the assume daemon.

    Owns the :class:`~assume.session.SessionCache` and implements all
    protocol actions. Has no awareness of socket transport.

    Parameters
    ----------
    max_size : int or None, optional
        Maximum number of sessions to retain in the cache. Forwarded
        to :class:`~assume.session.SessionCache`. Defaults to 10.
    """

    def __init__(self, max_size: int | None = None) -> None:
        self._cache: SessionCache = SessionCache(max_size=max_size)
        self._lock: threading.RLock = threading.RLock()

    def add(self, config: str) -> Dict[str, str]:
        """Initialize and cache a new session for a named config.

        Parameters
        ----------
        config : str
            The config name to load and cache.

        Returns
        -------
        Dict[str, str]
            Confirmation payload containing the config name.
        """

        with self._lock:
            self._cache[config] = Session(config)
            return {"config": config}

    def credentials(self, config: str) -> Dict[str, Any]:
        """Return the current temporary credentials for a cached session.

        Parameters
        ----------
        config : str
            The config name whose credentials to retrieve.

        Returns
        -------
        Dict[str, Any]
            The current AWS temporary credentials.

        Raises
        ------
        AssumeNotFoundError
            If no active session exists for the given config.
        """

        with self._lock:
            session = self._cache.get(config)
            if session is None:
                raise AssumeNotFoundError(
                    f"No active session for config '{config}'. "
                    "Initialize it first with 'add'."
                )
            return dict(session.session.credentials)

    def list(self) -> list[str]:
        """Return the names of all cached sessions.

        Returns
        -------
        list[str]
            Session names in recency order.
        """

        with self._lock:
            return list(self._cache.keys())

    def remove(self, config: str) -> Dict[str, str]:
        """Remove a cached session by config name.

        Parameters
        ----------
        config : str
            The config name to remove from the cache.

        Returns
        -------
        Dict[str, str]
            Confirmation payload containing the config name.

        Raises
        ------
        AssumeNotFoundError
            If no session for the given config is cached.
        """

        with self._lock:
            del self._cache[config]
            return {"config": config}

    def whoami(self, config: str) -> Dict[str, Any]:
        """Return the caller identity for a cached session.

        Parameters
        ----------
        config : str
            The config name whose caller identity to retrieve.

        Returns
        -------
        Dict[str, Any]
            The AWS STS caller identity (Account, Arn, UserId).

        Raises
        ------
        AssumeNotFoundError
            If no active session exists for the given config.
        """

        with self._lock:
            session = self._cache.get(config)
            if session is None:
                raise AssumeNotFoundError(
                    f"No active session for config '{config}'. "
                    "Initialize it first with 'add'."
                )
            result: Dict[str, Any] = session.session.client(
                "sts"
            ).get_caller_identity()
            result.pop("ResponseMetadata", None)
            return result

    def dispatch(self, request: RequestModel) -> Any:
        """Route a validated request to the appropriate handler.

        Parameters
        ----------
        request : RequestModel
            The incoming protocol request.

        Returns
        -------
        Any
            The handler's return value, used as the response ``data``
            field.

        Raises
        ------
        AssumeBadRequestError
            If a required payload field is missing or the action is
            unknown.
        AssumeNotFoundError
            If the requested session does not exist.
        """

        payload = request.payload

        def _cfg() -> str:
            try:
                return payload["config"]
            except KeyError:
                raise AssumeBadRequestError(
                    f"Action '{request.action}' requires"
                    " payload field 'config'."
                )

        match request.action:
            case "add":
                return self.add(_cfg())
            case "credentials":
                return self.credentials(_cfg())
            case "list":
                return self.list()
            case "remove":
                return self.remove(_cfg())
            case "whoami":
                return self.whoami(_cfg())
            case _:
                raise AssumeBadRequestError(
                    f"Unknown action: '{request.action}'"
                )


class Server:
    """UNIX socket server that accepts connections and dispatches to
    :class:`DaemonService`.

    Each connection is serviced in its own thread with one request per
    connection. The server socket is bound and listening after
    ``__init__`` returns; call :meth:`run` to start accepting.

    Parameters
    ----------
    constants : Constants
        Configuration including the socket path and connection backlog.
    service : DaemonService
        The business logic handler to delegate requests to.

    Raises
    ------
    OSError
        If a stale socket file exists and cannot be removed.
    """

    def __init__(
        self,
        constants: Constants,
        service: DaemonService,
    ) -> None:
        self._constants = constants
        self._service = service
        self._state_lock = threading.Lock()
        self._client_threads: set[threading.Thread] = set()
        self._connections: set[socket.socket] = set()
        self._running = threading.Event()

        self._prepare_socket_path()

        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(str(self._constants.socket_path))
        self._sock.settimeout(0.5)
        self._sock.listen(self._constants.max_unix_socket_connections)
        logger.info("Listening on %s", self._constants.socket_path)

    def _prepare_socket_path(self) -> None:
        """Validate and clear the socket path before binding.

        A few cases are handled explicitly:

        - Path does not exist: nothing to do.
        - Path exists but is not a socket: raises :class:`AssumeDaemonError`.
        - Path is a socket and a listener responds: raises
          :class:`AssumeDaemonError` (another daemon is running).
        - Path is a socket with no listener (``ConnectionRefusedError``) or
          one that vanished during the probe (``FileNotFoundError``): treated
          as a stale socket and removed or ignored respectively.
        - Any other ``OSError`` from the probe: raised as
          :class:`AssumeDaemonError` rather than unlinking blindly.

        Raises
        ------
        AssumeDaemonError
            If a live daemon occupies the path, the path is a non-socket
            file, or probing the socket yields an unexpected OS error.
        """

        path = self._constants.socket_path

        if not path.exists():
            return

        if not path.is_socket():
            raise AssumeDaemonError(
                f"Socket path {path!r} is occupied by a non-socket file."
            )

        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            probe.connect(str(path))
        except ConnectionRefusedError:
            pass  # no listener — stale socket, fall through to unlink
        except FileNotFoundError:
            return  # vanished between exists() and connect() — nothing to do
        except OSError as exc:
            raise AssumeDaemonError(
                f"Could not probe socket at {path!r}: {exc}"
            ) from exc
        else:
            raise AssumeDaemonError(
                f"A daemon is already running at {path!r}."
            )
        finally:
            probe.close()

        os.unlink(path)

    @staticmethod
    def _send(conn_file: Any, response: ResponseModel) -> None:
        conn_file.write(
            response.model_dump_json(exclude_none=True).encode("utf-8") + b"\n"
        )
        conn_file.flush()

    def _build_error_response(
        self,
        request_id: Any,
        exc: BaseAssumeError,
    ) -> ResponseModel:
        return ResponseModel(
            request_id=request_id,
            ok=False,
            error=ErrorModel(
                code=_error_code(exc),
                message=str(exc),
            ),
        )

    def _serve_one(self, conn_file: Any) -> bool:
        """Read one request from ``conn_file`` and write one response.

        Returns
        -------
        bool
            True if the ``kill`` action was processed, False otherwise.
        """

        try:
            raw = conn_file.readline()
        except OSError:
            return False

        if not raw:
            return False

        # parse the request envelope. generate a fresh request_id for
        # parse errors since no valid ID is available from the client.
        try:
            request = RequestModel.model_validate_json(raw.rstrip())
        except Exception as exc:
            response = ResponseModel(
                request_id=uuid4(),
                ok=False,
                error=ErrorModel(
                    code=400,
                    message=f"Invalid request: {exc}",
                ),
            )
            try:
                self._send(conn_file, response)
            except OSError:
                pass
            return False

        # kill is a transport-layer concern: signal the server to stop
        # after flushing the acknowledgement. DaemonService never sees it.
        if request.action == "kill":
            try:
                self._send(
                    conn_file,
                    ResponseModel(
                        request_id=request.request_id,
                        ok=True,
                    ),
                )
            except OSError:
                pass
            return True

        try:
            data = self._service.dispatch(request)
        except BaseAssumeError as exc:
            response = self._build_error_response(request.request_id, exc)
        except Exception as exc:
            logger.exception(
                "Unexpected error dispatching action '%s'",
                request.action,
            )
            response = ResponseModel(
                request_id=request.request_id,
                ok=False,
                error=ErrorModel(code=500, message=str(exc)),
            )
        else:
            response = ResponseModel(
                request_id=request.request_id,
                ok=True,
                data=data,
            )

        try:
            self._send(conn_file, response)
        except OSError:
            pass
        return False

    def _handle_client(self, conn: socket.socket) -> None:
        with self._state_lock:
            self._connections.add(conn)

        kill_requested = False
        try:
            with conn:
                conn_file = conn.makefile("rwb")
                with conn_file:
                    kill_requested = self._serve_one(conn_file)
        except Exception:
            logger.exception("Unhandled error in client thread")
        finally:
            with self._state_lock:
                self._connections.discard(conn)
                self._client_threads.discard(threading.current_thread())

        if kill_requested:
            self.stop()

    def _join_client_threads(self) -> None:
        with self._state_lock:
            threads = list(self._client_threads)
        for thread in threads:
            thread.join()

    def run(self) -> None:
        """Start the accept loop. Blocks until :meth:`stop` is called.

        Calls :meth:`stop` and joins all client threads on exit,
        regardless of how the loop exits.
        """

        self._running.set()
        try:
            while self._running.is_set():
                try:
                    conn, _ = self._sock.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._running.is_set():
                        raise
                    break

                thread = threading.Thread(
                    target=self._handle_client,
                    args=(conn,),
                    daemon=True,
                )
                with self._state_lock:
                    self._client_threads.add(thread)
                thread.start()
        finally:
            self.stop()
            self._join_client_threads()

    def stop(self) -> None:
        """Signal the server to stop and clean up resources.

        Sets the running flag, closes the server socket, shuts down
        active client connections, and removes the socket file.
        Returns immediately; :meth:`run` joins client threads on exit.
        Safe to call multiple times.
        """

        self._running.clear()

        try:
            self._sock.close()
        except OSError:
            pass

        with self._state_lock:
            connections = list(self._connections)

        for conn in connections:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                conn.close()
            except OSError:
                pass

        try:
            os.unlink(self._constants.socket_path)
        except FileNotFoundError:
            pass


class Client:
    """Short-lived UNIX socket client for sending one request to the
    daemon.

    Intended to be used as a context manager. One :class:`Client`
    instance sends one request then should be closed.

    Parameters
    ----------
    constants : Constants
        Configuration including the daemon socket path.

    Raises
    ------
    AssumeDaemonError
        If the connection cannot be established.
    """

    def __init__(self, constants: Constants) -> None:
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self._sock.connect(str(constants.socket_path))
        except OSError as exc:
            self._sock.close()
            raise AssumeDaemonError(
                f"Could not connect to daemon at"
                f" {constants.socket_path!r}: {exc}"
            ) from exc
        self._conn_file = self._sock.makefile("rwb")

    def send(
        self,
        action: str,
        payload: Dict[str, Any] | None = None,
    ) -> ResponseModel:
        """Send one request and return the parsed response.

        Parameters
        ----------
        action : str
            The daemon action to invoke.
        payload : Dict[str, Any] or None, optional
            Action-specific fields. Defaults to an empty dict.

        Returns
        -------
        ResponseModel
            The daemon's response envelope.

        Raises
        ------
        AssumeDaemonError
            If the daemon closes the connection without responding.
        """

        request = RequestModel(
            request_id=uuid4(),
            action=action,  # type: ignore[assignment]
            payload=payload or {},
        )
        self._conn_file.write(
            request.model_dump_json().encode("utf-8") + b"\n"
        )
        self._conn_file.flush()

        raw = self._conn_file.readline()
        if not raw:
            raise AssumeDaemonError(
                "Daemon closed the connection without a response."
            )
        return ResponseModel.model_validate_json(raw.rstrip())

    def close(self) -> None:
        """Close the underlying socket connection."""

        try:
            self._conn_file.close()
        except OSError:
            pass
        try:
            self._sock.close()
        except OSError:
            pass

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
