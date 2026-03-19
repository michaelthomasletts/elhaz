# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Create refreshable AWS sessions and cache them with LRU-like behavior."""

__all__ = ["Session", "SessionCache"]

from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Iterator, Tuple

from boto3_refresh_session import STSRefreshableSession

from .config import Config
from .exceptions import ElhazNotFoundError, ElhazValidationError


class Session:
    """Represent a named refreshable AWS session.

    Parameters
    ----------
    name : str
        The persisted config name used to initialize the refreshable session.

    Attributes
    ----------
    created_at : datetime
        UTC timestamp for when the session object was created.
    expires_at : datetime
        UTC expiration timestamp parsed from current temporary credentials.
    last_accessed : datetime
        UTC timestamp of the most recent attribute retrieval.
    name : str
        Immutable session label.
    session : STSRefreshableSession
        The underlying refreshable session object providing AWS credentials.
    """

    def __init__(self, name: str) -> None:
        """Initialize a named session from persisted config."""

        self._name = name
        self._created_at: datetime = datetime.now(timezone.utc)
        self._last_accessed: datetime = self.created_at
        self._session = STSRefreshableSession(**Config(name).config)

    def __getattribute__(self, name: str) -> Any:
        """Return an attribute and update the access timestamp.

        Notes
        -----
        ``last_accessed`` is excluded to avoid mutating state when merely
        reading the timestamp itself.
        """

        value = super().__getattribute__(name)
        if name not in ("_last_accessed", "last_accessed") and (
            "_last_accessed" in super().__getattribute__("__dict__")
        ):
            self._last_accessed = datetime.now(timezone.utc)
        return value

    @property
    def name(self) -> str:
        """Return the immutable session name."""

        return self._name

    @name.setter
    def name(self, _: str) -> None:
        """Reject direct session name changes."""

        raise ElhazValidationError(
            "Session name cannot be changed after creation."
        )

    @property
    def created_at(self) -> datetime:
        """Return the UTC creation timestamp."""

        return self._created_at

    @created_at.setter
    def created_at(self, _: datetime) -> None:
        """Reject direct creation timestamp changes."""

        raise ElhazValidationError(
            "Session creation time cannot be changed after creation."
        )

    @property
    def expires_at(self) -> datetime:
        """Return the UTC credentials expiration timestamp."""

        expiry_time: str = self.session.credentials["expiry_time"]
        return datetime.fromisoformat(expiry_time.replace("Z", "+00:00"))

    @expires_at.setter
    def expires_at(self, _: datetime) -> None:
        """Reject direct expiration timestamp changes."""

        raise ElhazValidationError(
            "Session expiration time cannot be changed after creation."
        )

    @property
    def last_accessed(self) -> datetime:
        """Return the UTC timestamp of the latest attribute access."""

        return self._last_accessed

    @last_accessed.setter
    def last_accessed(self, _: datetime) -> None:
        """Reject direct access timestamp changes."""

        raise ElhazValidationError(
            "Session last accessed time cannot be changed directly."
        )

    @property
    def session(self) -> STSRefreshableSession:
        """Return the underlying refreshable session object."""

        return self._session


class SessionCache:
    """Store named sessions with bounded size and recency ordering.

    Parameters
    ----------
    max_size : int | None, optional
        Maximum number of sessions to retain. Defaults to 10.

    Attributes
    ----------
    cache : OrderedDict[str, Session]
        Internal mapping of session names to session objects, ordered by
        recency of access (most recent at the end). LRU eviction. Bounded by
        max_size.
    max_size : int
        The maximum number of sessions the cache can hold. Setting this value
        will trigger eviction of least recently accessed sessions if the
        current cache size exceeds the new max_size.

    Methods
    -------
    clear() -> None
        Remove all sessions from the cache.
    copy() -> "SessionCache"
        Return a shallow copy of the session cache.
    get(name: str, default: Session | None = None) -> Session | None
        Return a session by name and update its recency, or return default if
        not found.
    items() -> Iterator[Tuple[str, Session]]
        Return an iterator over (name, session) pairs in recency order.
    keys() -> Iterator[str]
        Return an iterator over session names in recency order.
    pop(name: str) -> Session
        Remove and return a session by name, or raise an error if not found.
    popitem(last: bool = True) -> Tuple[str, Session]
        Remove and return a (name, session) pair based on recency, or raise an
        error if the cache is empty.
    values() -> Iterator[Session]
        Return an iterator over sessions in recency order.
    """

    def __init__(self, max_size: int | None = None) -> None:
        """Initialize an empty cache with a configured maximum size."""

        self.cache: OrderedDict[str, Session] = OrderedDict()
        self.max_size = max_size or 10

    @property
    def max_size(self) -> int:
        """Return the cache capacity."""

        return self._max_size

    @max_size.setter
    def max_size(self, value: int) -> None:
        """Set cache capacity and evict oldest entries if needed."""

        if value == 0:
            raise ElhazValidationError(
                "Cache max_size must be greater than zero."
            )

        self._max_size = abs(value)
        while len(self.cache) > self._max_size:
            self.cache.popitem(last=False)

    def __contains__(self, name: str) -> bool:
        """Return True if a session with the given name exists in the cache."""

        return name in self.cache

    def __delitem__(self, name: str) -> None:
        """Remove a session from the cache by name.

        Parameters
        ----------
        name : str
            The session name to remove from the cache.

        Raises
        ------
        ElhazNotFoundError
            If no session with the specified name exists in the cache.
        """

        try:
            del self.cache[name]
        except KeyError as exc:
            raise ElhazNotFoundError(
                f"No session found with name {name!r} to delete."
            ) from exc

    def __getitem__(self, name: str) -> Session:
        """Return a session by name and update its recency.

        Parameters
        ----------
        name : str
            The session name to retrieve.

        Returns
        -------
        Session
            The session object associated with the given name.

        Raises
        ------
        ElhazNotFoundError
            If no session with the specified name exists in the cache.
        """

        try:
            session = self.cache[name]
            self.cache.move_to_end(name)
            return session
        except KeyError as exc:
            raise ElhazNotFoundError(
                f"No session found with name {name!r}."
            ) from exc

    def __iter__(self) -> Iterator[Tuple[str, Session]]:
        """Return an iterator over (name, session) pairs in recency order."""

        return iter(self.cache.items())

    def __len__(self) -> int:
        """Return the number of sessions currently in the cache."""

        return len(self.cache)

    def __reversed__(self) -> Iterator[Tuple[str, Session]]:
        """Return a reverse iterator over (name, session) pairs in recency
        order.
        """

        return iter(reversed(self.cache.items()))

    def __setitem__(self, name: str, session: Session) -> None:
        """Add a session to the cache and evict oldest if capacity is exceeded.

        Parameters
        ----------
        name : str
            The name of the session to add to the cache.
        session : Session
            The session object to add to the cache.
        """

        try:
            assert session.name == name
        except AssertionError as exc:
            raise ElhazValidationError(
                f"Session name {session.name!r} does not match cache key "
                f"{name!r}."
            ) from exc

        self.cache[name] = session
        self.cache.move_to_end(name)
        while len(self.cache) > self._max_size:
            self.cache.popitem(last=False)

    def clear(self) -> None:
        """Remove all sessions from the cache."""

        self.cache.clear()

    def copy(self) -> "SessionCache":
        """Return a shallow copy of the session cache."""

        new_cache = SessionCache(max_size=self.max_size)
        new_cache.cache = self.cache.copy()
        return new_cache

    def get(self, name: str, default: Session | None = None) -> Session | None:
        """Return a session by name and update its recency.

        Parameters
        ----------
        name : str
            The session name to retrieve.
        default : Session | None, optional
            The value to return if no session with the specified name exists.

        Returns
        -------
        Session | None
            The session object associated with the given name, or the default
            value if not found.
        """

        try:
            return self.__getitem__(name)
        except ElhazNotFoundError:
            return default

    def items(self) -> Iterator[Tuple[str, Session]]:
        """Return an iterator over (name, session) pairs in recency order."""

        return iter(self.cache.items())

    def keys(self) -> Iterator[str]:
        """Return an iterator over session names in recency order."""

        return iter(self.cache.keys())

    def pop(self, name: str) -> Session:
        """Remove and return a session by name.

        Parameters
        ----------
        name : str
            The session name to remove and return.

        Returns
        -------
        Session
            The session object that was removed from the cache.

        Raises
        ------
        ElhazNotFoundError
            If no session with the specified name exists in the cache.
        """

        try:
            return self.cache.pop(name)
        except KeyError as exc:
            raise ElhazNotFoundError(
                f"No session found with name {name!r} to pop."
            ) from exc

    def popitem(self, last: bool = True) -> Tuple[str, Session]:
        """Remove and return a (name, session) pair.

        Parameters
        ----------
        last : bool, optional
            If True, remove the most recently accessed session; if False,
            remove the least recently accessed session. Defaults to True.

        Returns
        -------
        Tuple[str, Session]
            The (name, session) pair that was removed from the cache.

        Raises
        ------
        ElhazNotFoundError
            If the cache is empty.
        """

        try:
            return self.cache.popitem(last=last)
        except KeyError as exc:
            raise ElhazNotFoundError("No sessions available to pop.") from exc

    def values(self) -> Iterator[Session]:
        """Return an iterator over sessions in recency order."""

        return iter(self.cache.values())
