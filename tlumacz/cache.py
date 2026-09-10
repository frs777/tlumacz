"""Translation cache using SQLite for persistent storage.

Caches translated chunks to avoid redundant API calls for repeated content.
Common in technical documents with recurring headers, footers, and terminology.

Cache key is a hash of: chunk_text + system_prompt + skill_text + model + temperature.
This ensures the same input with different configurations produces different cache entries.
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
from pathlib import Path
from typing import Optional


DEFAULT_CACHE_DIR = Path.home() / ".config" / "tlumacz"
DEFAULT_CACHE_DB = "cache.db"


class TranslationCache:
    """Thread-safe SQLite-backed translation cache.

    Usage:
        cache = TranslationCache()
        result = cache.get(chunk, system_prompt, skill_text, model, temperature)
        if result is None:
            result = translate(chunk)
            cache.put(chunk, system_prompt, skill_text, model, temperature, result)

    Cache automatically cleans up entries older than MAX_AGE_DAYS on init.
    """

    # Remove entries older than 7 days to keep cache size reasonable
    MAX_AGE_DAYS = 7

    def __init__(self, cache_dir: Optional[Path] = None, enabled: bool = True) -> None:
        self._enabled = enabled
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._hits = 0
        self._misses = 0

        if not enabled:
            return

        cache_dir = cache_dir or DEFAULT_CACHE_DIR
        cache_dir.mkdir(parents=True, exist_ok=True)
        db_path = cache_dir / DEFAULT_CACHE_DB

        try:
            self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    key TEXT PRIMARY KEY,
                    translation TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.commit()
            self._cleanup_old_entries()
        except OSError:
            # If we can't create the cache, disable it silently
            self._enabled = False
            self._conn = None

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than MAX_AGE_DAYS."""
        if self._conn is None:
            return
        try:
            self._conn.execute(
                f"DELETE FROM translations WHERE created_at < datetime('now', '-{self.MAX_AGE_DAYS} days')"
            )
            self._conn.commit()
        except sqlite3.Error:
            pass

    def _make_key(
        self,
        chunk: str,
        system_prompt: str,
        skill_text: str,
        model: str,
        temperature: float,
    ) -> str:
        """Create a deterministic cache key from all translation inputs."""
        combined = f"{chunk}|{system_prompt}|{skill_text}|{model}|{temperature}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def get(
        self,
        chunk: str,
        system_prompt: str,
        skill_text: str,
        model: str,
        temperature: float,
    ) -> Optional[str]:
        """Look up a cached translation. Returns None if not found or cache disabled."""
        if not self._enabled or self._conn is None:
            return None

        key = self._make_key(chunk, system_prompt, skill_text, model, temperature)
        with self._lock:
            try:
                cursor = self._conn.execute(
                    "SELECT translation FROM translations WHERE key = ?", (key,)
                )
                row = cursor.fetchone()
                if row:
                    self._hits += 1
                    return row[0]
                else:
                    self._misses += 1
                    return None
            except sqlite3.Error:
                self._misses += 1
                return None

    def put(
        self,
        chunk: str,
        system_prompt: str,
        skill_text: str,
        model: str,
        temperature: float,
        translation: str,
    ) -> None:
        """Store a translation in the cache. Silently fails if cache disabled."""
        if not self._enabled or self._conn is None:
            return

        key = self._make_key(chunk, system_prompt, skill_text, model, temperature)
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT OR REPLACE INTO translations (key, translation) VALUES (?, ?)",
                    (key, translation),
                )
                self._conn.commit()
            except sqlite3.Error:
                pass

    def clear(self) -> None:
        """Remove all cached translations."""
        if not self._enabled or self._conn is None:
            return

        with self._lock:
            try:
                self._conn.execute("DELETE FROM translations")
                self._conn.commit()
            except sqlite3.Error:
                pass

    def stats(self) -> dict[str, int]:
        """Return cache statistics (entry count, hits, misses)."""
        if not self._enabled or self._conn is None:
            return {"entries": 0, "enabled": False, "hits": 0, "misses": 0}

        with self._lock:
            try:
                cursor = self._conn.execute("SELECT COUNT(*) FROM translations")
                count = cursor.fetchone()[0]
                return {
                    "entries": count,
                    "enabled": True,
                    "hits": self._hits,
                    "misses": self._misses,
                }
            except sqlite3.Error:
                return {"entries": 0, "enabled": True, "hits": self._hits, "misses": self._misses}

    def reset_stats(self) -> None:
        """Reset hit/miss counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            with self._lock:
                try:
                    self._conn.close()
                except sqlite3.Error:
                    pass
            self._conn = None
