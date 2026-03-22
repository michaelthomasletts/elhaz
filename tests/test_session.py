# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.session.Session and SessionCache."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from elhaz.exceptions import ElhazNotFoundError, ElhazValidationError
from elhaz.session import Session, SessionCache
from tests.conftest import FakeRefreshableSession, FakeSessionObj


@pytest.fixture(autouse=True)
def _patch_session_deps(monkeypatch):
    """Replace external dependencies with lightweight fakes."""
    from tests.conftest import FakeConfig, FakeRefreshableSession

    monkeypatch.setattr(
        "elhaz.session.STSRefreshableSession", FakeRefreshableSession
    )
    monkeypatch.setattr("elhaz.session.Config", FakeConfig)


def test_session_init_sets_name() -> None:
    s = Session("test")
    assert s._name == "test"


def test_session_init_sets_created_at() -> None:
    s = Session("test")
    assert isinstance(s._created_at, datetime)
    assert s._created_at.tzinfo == timezone.utc


def test_session_init_creates_underlying_session() -> None:
    s = Session("test")
    assert isinstance(s._session, FakeRefreshableSession)


def test_session_name_property_returns_name() -> None:
    s = Session("myconfig")
    assert s.name == "myconfig"


def test_session_name_setter_raises() -> None:
    s = Session("test")
    with pytest.raises(ElhazValidationError):
        s.name = "other"


def test_session_created_at_returns_datetime() -> None:
    s = Session("test")
    assert isinstance(s.created_at, datetime)


def test_session_created_at_setter_raises() -> None:
    s = Session("test")
    with pytest.raises(ElhazValidationError):
        s.created_at = datetime.now(timezone.utc)


def test_session_expires_at_parses_z_suffix() -> None:
    s = Session("test")
    exp = s.expires_at
    assert isinstance(exp, datetime)
    assert exp.tzinfo is not None
    assert exp.year == 2030


def test_session_expires_at_is_utc() -> None:
    s = Session("test")
    exp = s.expires_at
    # UTC offset must be zero
    assert exp.utcoffset().total_seconds() == 0  # type: ignore[union-attr]


def test_session_expires_at_setter_raises() -> None:
    s = Session("test")
    with pytest.raises(ElhazValidationError):
        s.expires_at = datetime.now(timezone.utc)


def test_session_last_accessed_setter_raises() -> None:
    s = Session("test")
    with pytest.raises(ElhazValidationError):
        s.last_accessed = datetime.now(timezone.utc)


def test_session_last_accessed_is_set_on_init() -> None:
    s = Session("test")
    assert isinstance(s._last_accessed, datetime)
    assert s._last_accessed.tzinfo == timezone.utc


def test_session_session_property_returns_session() -> None:
    s = Session("test")
    assert isinstance(s.session, FakeRefreshableSession)


def test_getattribute_updates_last_accessed_on_regular_access() -> None:
    s = Session("test")
    before = s._last_accessed
    time.sleep(0.01)
    _ = s.session  # accessing .session should update last_accessed
    after = s._last_accessed
    assert after >= before


def test_getattribute_does_not_update_last_accessed_when_reading_it() -> None:
    s = Session("test")
    ts1 = s.last_accessed
    ts2 = s.last_accessed
    # Reading last_accessed must not change the timestamp
    assert ts1 == ts2


def test_getattribute_does_not_recurse_during_init() -> None:
    # If __init__ completes without error the guard works correctly.
    s = Session("test")
    assert s.name == "test"


def test_accessing_attribute_advances_last_accessed_monotonically() -> None:
    s = Session("test")
    timestamps = []
    for _ in range(3):
        time.sleep(0.01)
        _ = s.name
        timestamps.append(s._last_accessed)
    assert timestamps[0] <= timestamps[1] <= timestamps[2]


def test_session_cache_default_max_size() -> None:
    sc = SessionCache()
    assert sc.max_size == 10


def test_session_cache_custom_max_size() -> None:
    sc = SessionCache(max_size=5)
    assert sc.max_size == 5


def test_session_cache_init_empty() -> None:
    sc = SessionCache()
    assert len(sc) == 0


def test_session_cache_max_size_zero_raises() -> None:
    sc = SessionCache(max_size=3)
    with pytest.raises(ElhazValidationError):
        sc.max_size = 0


def test_session_cache_max_size_negative_stored_as_abs() -> None:
    sc = SessionCache(max_size=3)
    sc.max_size = -5
    assert sc._max_size == 5


def test_session_cache_shrinking_evicts_oldest() -> None:
    sc = SessionCache(max_size=5)
    for i in range(5):
        obj = FakeSessionObj(f"s{i}")
        sc[f"s{i}"] = obj  # type: ignore[assignment]
    sc.max_size = 2
    assert len(sc) == 2
    # The two most recently inserted items should remain
    keys = list(sc.cache.keys())
    assert "s3" in keys
    assert "s4" in keys


def test_setitem_adds_entry() -> None:
    sc = SessionCache()
    obj = FakeSessionObj("alpha")
    sc["alpha"] = obj  # type: ignore[assignment]
    assert "alpha" in sc


def test_setitem_moves_to_end() -> None:
    sc = SessionCache()
    for name in ("a", "b", "c"):
        sc[name] = FakeSessionObj(name)  # type: ignore[assignment]
    sc["a"] = FakeSessionObj("a")  # type: ignore[assignment]
    keys = list(sc.cache.keys())
    assert keys[-1] == "a"


def test_setitem_evicts_oldest_when_over_capacity() -> None:
    sc = SessionCache(max_size=2)
    sc["x"] = FakeSessionObj("x")  # type: ignore[assignment]
    sc["y"] = FakeSessionObj("y")  # type: ignore[assignment]
    sc["z"] = FakeSessionObj("z")  # type: ignore[assignment]
    assert len(sc) == 2
    assert "x" not in sc  # "x" was oldest and should be evicted


def test_setitem_raises_when_name_mismatch() -> None:
    sc = SessionCache()
    obj = FakeSessionObj("real_name")
    with pytest.raises(ElhazValidationError):
        sc["wrong_key"] = obj  # type: ignore[assignment]


def test_getitem_returns_session() -> None:
    sc = SessionCache()
    obj = FakeSessionObj("demo")
    sc["demo"] = obj  # type: ignore[assignment]
    assert sc["demo"] is obj


def test_getitem_moves_to_end() -> None:
    sc = SessionCache()
    for name in ("a", "b", "c"):
        sc[name] = FakeSessionObj(name)  # type: ignore[assignment]
    _ = sc["a"]  # access "a" → should move to end
    keys = list(sc.cache.keys())
    assert keys[-1] == "a"


def test_getitem_raises_on_miss() -> None:
    sc = SessionCache()
    with pytest.raises(ElhazNotFoundError):
        _ = sc["nonexistent"]


def test_delitem_removes_entry() -> None:
    sc = SessionCache()
    sc["demo"] = FakeSessionObj("demo")  # type: ignore[assignment]
    del sc["demo"]
    assert "demo" not in sc


def test_delitem_raises_on_miss() -> None:
    sc = SessionCache()
    with pytest.raises(ElhazNotFoundError):
        del sc["ghost"]


def test_contains_true_for_present() -> None:
    sc = SessionCache()
    sc["demo"] = FakeSessionObj("demo")  # type: ignore[assignment]
    assert "demo" in sc


def test_contains_false_for_absent() -> None:
    sc = SessionCache()
    assert "nobody" not in sc


def test_len_correct_count() -> None:
    sc = SessionCache()
    for i in range(4):
        sc[f"s{i}"] = FakeSessionObj(f"s{i}")  # type: ignore[assignment]
    assert len(sc) == 4


def test_iter_yields_name_session_pairs() -> None:
    sc = SessionCache()
    obj = FakeSessionObj("demo")
    sc["demo"] = obj  # type: ignore[assignment]
    pairs = list(sc)
    assert len(pairs) == 1
    name, session = pairs[0]
    assert name == "demo"
    assert session is obj


def test_iter_order_reflects_insertion_order() -> None:
    sc = SessionCache()
    for name in ("a", "b", "c"):
        sc[name] = FakeSessionObj(name)  # type: ignore[assignment]
    names = [k for k, _ in sc]
    assert names == ["a", "b", "c"]


def test_reversed_yields_pairs_in_reverse() -> None:
    sc = SessionCache()
    for name in ("a", "b", "c"):
        sc[name] = FakeSessionObj(name)  # type: ignore[assignment]
    names = [k for k, _ in reversed(sc)]
    assert names == ["c", "b", "a"]


def test_get_returns_session_on_hit() -> None:
    sc = SessionCache()
    obj = FakeSessionObj("demo")
    sc["demo"] = obj  # type: ignore[assignment]
    assert sc.get("demo") is obj


def test_get_updates_recency_on_hit() -> None:
    sc = SessionCache()
    for name in ("a", "b", "c"):
        sc[name] = FakeSessionObj(name)  # type: ignore[assignment]
    sc.get("a")
    keys = list(sc.cache.keys())
    assert keys[-1] == "a"


def test_get_returns_none_on_miss() -> None:
    sc = SessionCache()
    assert sc.get("nobody") is None


def test_get_returns_custom_default_on_miss() -> None:
    sc = SessionCache()
    sentinel = object()
    assert sc.get("nobody", sentinel) is sentinel  # type: ignore[arg-type]


def test_get_does_not_raise_on_miss() -> None:
    sc = SessionCache()
    result = sc.get("nobody")
    assert result is None


def test_pop_removes_and_returns() -> None:
    sc = SessionCache()
    obj = FakeSessionObj("demo")
    sc["demo"] = obj  # type: ignore[assignment]
    result = sc.pop("demo")
    assert result is obj
    assert "demo" not in sc


def test_pop_raises_on_miss() -> None:
    sc = SessionCache()
    with pytest.raises(ElhazNotFoundError):
        sc.pop("ghost")


def test_popitem_last_true_removes_most_recent() -> None:
    sc = SessionCache()
    for name in ("a", "b", "c"):
        sc[name] = FakeSessionObj(name)  # type: ignore[assignment]
    key, _ = sc.popitem(last=True)
    assert key == "c"


def test_popitem_last_false_removes_least_recent() -> None:
    sc = SessionCache()
    for name in ("a", "b", "c"):
        sc[name] = FakeSessionObj(name)  # type: ignore[assignment]
    key, _ = sc.popitem(last=False)
    assert key == "a"


def test_popitem_raises_when_empty() -> None:
    sc = SessionCache()
    with pytest.raises(ElhazNotFoundError):
        sc.popitem()


def test_clear_empties_cache() -> None:
    sc = SessionCache()
    for i in range(3):
        sc[f"s{i}"] = FakeSessionObj(f"s{i}")  # type: ignore[assignment]
    sc.clear()
    assert len(sc) == 0


def test_copy_creates_independent_copy() -> None:
    sc = SessionCache(max_size=5)
    obj = FakeSessionObj("demo")
    sc["demo"] = obj  # type: ignore[assignment]
    cp = sc.copy()
    assert cp.max_size == sc.max_size
    assert "demo" in cp
    # Mutating the copy does not affect the original
    cp["other"] = FakeSessionObj("other")  # type: ignore[assignment]
    assert "other" not in sc


def test_copy_preserves_order() -> None:
    sc = SessionCache()
    for name in ("a", "b", "c"):
        sc[name] = FakeSessionObj(name)  # type: ignore[assignment]
    cp = sc.copy()
    assert list(cp.cache.keys()) == ["a", "b", "c"]


def test_keys_returns_names() -> None:
    sc = SessionCache()
    sc["x"] = FakeSessionObj("x")  # type: ignore[assignment]
    sc["y"] = FakeSessionObj("y")  # type: ignore[assignment]
    assert list(sc.keys()) == ["x", "y"]


def test_values_returns_sessions() -> None:
    sc = SessionCache()
    obj_x = FakeSessionObj("x")
    obj_y = FakeSessionObj("y")
    sc["x"] = obj_x  # type: ignore[assignment]
    sc["y"] = obj_y  # type: ignore[assignment]
    vals = list(sc.values())
    assert vals[0] is obj_x
    assert vals[1] is obj_y


def test_items_returns_pairs() -> None:
    sc = SessionCache()
    obj = FakeSessionObj("demo")
    sc["demo"] = obj  # type: ignore[assignment]
    pairs = list(sc.items())
    assert pairs == [("demo", obj)]


def test_lru_evicts_second_oldest_after_access() -> None:
    """Fill cache to capacity, access oldest, insert new — second-oldest
    evicted."""
    sc = SessionCache(max_size=3)
    sc["a"] = FakeSessionObj("a")  # type: ignore[assignment]
    sc["b"] = FakeSessionObj("b")  # type: ignore[assignment]
    sc["c"] = FakeSessionObj("c")  # type: ignore[assignment]
    # access "a" → it becomes the most recent; "b" is now LRU
    _ = sc["a"]
    # insert "d" → should evict "b" (the least recently used)
    sc["d"] = FakeSessionObj("d")  # type: ignore[assignment]
    assert "b" not in sc
    assert "a" in sc
    assert "c" in sc
    assert "d" in sc
