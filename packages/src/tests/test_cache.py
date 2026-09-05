"""Tests for the translation cache."""

import tempfile
from pathlib import Path

import pytest

from tlumacz.cache import TranslationCache


@pytest.fixture
def cache_dir(tmp_path):
    """Provide a temporary cache directory."""
    return tmp_path / "cache"


def test_cache_put_and_get(cache_dir):
    """Cache should store and retrieve translations."""
    cache = TranslationCache(cache_dir=cache_dir)

    chunk = "Hello world"
    system = "Translate to Polish"
    skill = ""
    model = "test-model"
    temp = 0.1
    translation = "Witaj świecie"

    # Initially empty
    assert cache.get(chunk, system, skill, model, temp) is None

    # Store translation
    cache.put(chunk, system, skill, model, temp, translation)

    # Retrieve it
    result = cache.get(chunk, system, skill, model, temp)
    assert result == translation

    cache.close()


def test_cache_key_includes_all_params(cache_dir):
    """Different parameters should produce different cache keys."""
    cache = TranslationCache(cache_dir=cache_dir)

    chunk = "Hello"
    translation1 = "Cześć"
    translation2 = "Witaj"

    # Same chunk, different model
    cache.put(chunk, "sys", "", "model-a", 0.1, translation1)
    cache.put(chunk, "sys", "", "model-b", 0.1, translation2)

    assert cache.get(chunk, "sys", "", "model-a", 0.1) == translation1
    assert cache.get(chunk, "sys", "", "model-b", 0.1) == translation2

    cache.close()


def test_cache_clear(cache_dir):
    """clear() should remove all entries."""
    cache = TranslationCache(cache_dir=cache_dir)

    cache.put("a", "sys", "", "m", 0.1, "A")
    cache.put("b", "sys", "", "m", 0.1, "B")
    assert cache.stats()["entries"] == 2

    cache.clear()
    assert cache.stats()["entries"] == 0
    assert cache.get("a", "sys", "", "m", 0.1) is None

    cache.close()


def test_cache_disabled():
    """Disabled cache should not store or retrieve anything."""
    cache = TranslationCache(enabled=False)

    cache.put("test", "sys", "", "m", 0.1, "translation")
    assert cache.get("test", "sys", "", "m", 0.1) is None
    assert cache.stats()["enabled"] is False

    cache.close()


def test_cache_persistence(cache_dir):
    """Cache should persist across instances."""
    # First instance: store
    cache1 = TranslationCache(cache_dir=cache_dir)
    cache1.put("test", "sys", "", "m", 0.1, "persisted")
    cache1.close()

    # Second instance: retrieve
    cache2 = TranslationCache(cache_dir=cache_dir)
    result = cache2.get("test", "sys", "", "m", 0.1)
    assert result == "persisted"
    cache2.close()


def test_cache_stats(cache_dir):
    """stats() should return entry count and hit/miss counters."""
    cache = TranslationCache(cache_dir=cache_dir)

    assert cache.stats() == {"entries": 0, "enabled": True, "hits": 0, "misses": 0}

    cache.put("a", "sys", "", "m", 0.1, "A")
    assert cache.stats()["entries"] == 1

    # Miss (not in cache)
    cache.get("b", "sys", "", "m", 0.1)
    assert cache.stats()["misses"] == 1

    # Hit (in cache)
    cache.get("a", "sys", "", "m", 0.1)
    assert cache.stats()["hits"] == 1

    cache.close()


def test_cache_reset_stats(cache_dir):
    """reset_stats() should clear hit/miss counters."""
    cache = TranslationCache(cache_dir=cache_dir)

    cache.put("a", "sys", "", "m", 0.1, "A")
    cache.get("a", "sys", "", "m", 0.1)  # hit
    cache.get("b", "sys", "", "m", 0.1)  # miss

    assert cache.stats()["hits"] == 1
    assert cache.stats()["misses"] == 1

    cache.reset_stats()
    assert cache.stats()["hits"] == 0
    assert cache.stats()["misses"] == 0

    cache.close()


def test_cache_overwrite(cache_dir):
    """Putting the same key twice should overwrite."""
    cache = TranslationCache(cache_dir=cache_dir)

    cache.put("test", "sys", "", "m", 0.1, "first")
    cache.put("test", "sys", "", "m", 0.1, "second")

    assert cache.get("test", "sys", "", "m", 0.1) == "second"
    assert cache.stats()["entries"] == 1

    cache.close()


def test_cache_thread_safety(cache_dir):
    """Cache should handle concurrent access safely."""
    import threading

    cache = TranslationCache(cache_dir=cache_dir)
    errors = []

    def writer(n):
        try:
            for i in range(10):
                cache.put(f"chunk-{n}-{i}", "sys", "", "m", 0.1, f"trans-{n}-{i}")
        except Exception as e:
            errors.append(e)

    def reader(n):
        try:
            for i in range(10):
                cache.get(f"chunk-{n}-{i}", "sys", "", "m", 0.1)
        except Exception as e:
            errors.append(e)

    threads = []
    for n in range(5):
        threads.append(threading.Thread(target=writer, args=(n,)))
        threads.append(threading.Thread(target=reader, args=(n,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread safety errors: {errors}"
    cache.close()


def test_cache_auto_cleanup(cache_dir):
    """Old entries should be removed on init."""
    import sqlite3
    from datetime import datetime, timedelta

    # Create cache and add entry
    cache1 = TranslationCache(cache_dir=cache_dir)
    cache1.put("test", "sys", "", "m", 0.1, "translation")
    cache1.close()

    # Manually set created_at to 10 days ago
    db_path = cache_dir / "cache.db"
    conn = sqlite3.connect(str(db_path))
    old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE translations SET created_at = ?", (old_date,))
    conn.commit()
    conn.close()

    # New cache instance should clean up old entry
    cache2 = TranslationCache(cache_dir=cache_dir)
    assert cache2.get("test", "sys", "", "m", 0.1) is None
    assert cache2.stats()["entries"] == 0
    cache2.close()
