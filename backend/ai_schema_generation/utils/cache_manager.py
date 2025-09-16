"""
T060: Intelligent caching system
Caching system for AI analysis results, schemas, and processed documents
"""

import json
import hashlib
import pickle
import time
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: datetime
    tags: List[str]
    size_bytes: int


class CacheManager:
    """Intelligent caching system with SQLite backend"""

    def __init__(self, cache_dir: str = "data/cache", max_size_mb: int = 500):
        """Initialize cache manager"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cache.db"
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.setup_database()

    def setup_database(self):
        """Setup cache database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    file_path TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    tags TEXT,
                    size_bytes INTEGER,
                    content_hash TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires
                ON cache_entries (expires_at)
            """)

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache entry"""
        return self.cache_dir / f"{key}.cache"

    def set(self, key: str, value: Any, ttl_hours: Optional[int] = None,
            tags: Optional[List[str]] = None) -> bool:
        """Set cache entry"""
        try:
            file_path = self._get_file_path(key)

            # Serialize value
            with open(file_path, 'wb') as f:
                pickle.dump(value, f)

            size_bytes = file_path.stat().st_size
            content_hash = hashlib.md5(file_path.read_bytes()).hexdigest()

            # Calculate expiration
            expires_at = None
            if ttl_hours:
                expires_at = datetime.now() + timedelta(hours=ttl_hours)

            # Store metadata
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries
                    (key, file_path, created_at, expires_at, access_count,
                     last_accessed, tags, size_bytes, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key,
                    str(file_path),
                    datetime.now().isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    0,
                    datetime.now().isoformat(),
                    json.dumps(tags or []),
                    size_bytes,
                    content_hash
                ))

            # Cleanup if cache is too large
            self._cleanup_if_needed()
            return True

        except Exception:
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get cache entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_path, expires_at FROM cache_entries
                    WHERE key = ?
                """, (key,))

                row = cursor.fetchone()
                if not row:
                    return None

                file_path, expires_at = row

                # Check expiration
                if expires_at:
                    exp_time = datetime.fromisoformat(expires_at)
                    if datetime.now() > exp_time:
                        self.delete(key)
                        return None

                # Load value
                with open(file_path, 'rb') as f:
                    value = pickle.load(f)

                # Update access stats
                conn.execute("""
                    UPDATE cache_entries
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE key = ?
                """, (datetime.now().isoformat(), key))

                return value

        except Exception:
            return None

    def delete(self, key: str) -> bool:
        """Delete cache entry"""
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))

            return True
        except Exception:
            return False

    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear cache entries by tags"""
        cleared = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key, tags FROM cache_entries")

            for key, tags_json in cursor.fetchall():
                try:
                    entry_tags = json.loads(tags_json or '[]')
                    if any(tag in entry_tags for tag in tags):
                        if self.delete(key):
                            cleared += 1
                except Exception:
                    continue

        return cleared

    def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        cleaned = 0
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT key FROM cache_entries
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (now,))

            for (key,) in cursor.fetchall():
                if self.delete(key):
                    cleaned += 1

        return cleaned

    def _cleanup_if_needed(self):
        """Cleanup cache if it exceeds size limit"""
        current_size = self.get_cache_size()

        if current_size > self.max_size_bytes:
            # Remove least recently used entries
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT key FROM cache_entries
                    ORDER BY last_accessed ASC
                    LIMIT 100
                """)

                for (key,) in cursor.fetchall():
                    self.delete(key)
                    current_size = self.get_cache_size()
                    if current_size <= self.max_size_bytes * 0.8:  # 80% threshold
                        break

    def get_cache_size(self) -> int:
        """Get total cache size in bytes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
            result = cursor.fetchone()[0]
            return result or 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*), SUM(size_bytes), SUM(access_count)
                FROM cache_entries
            """)
            entry_count, total_size, total_accesses = cursor.fetchone()

            cursor = conn.execute("""
                SELECT COUNT(*) FROM cache_entries
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (datetime.now().isoformat(),))
            expired_count = cursor.fetchone()[0]

        return {
            'total_entries': entry_count or 0,
            'total_size_bytes': total_size or 0,
            'total_size_mb': (total_size or 0) / (1024 * 1024),
            'total_accesses': total_accesses or 0,
            'expired_entries': expired_count or 0,
            'hit_ratio': self._calculate_hit_ratio()
        }

    def _calculate_hit_ratio(self) -> float:
        """Calculate cache hit ratio (placeholder)"""
        # In a real implementation, this would track hits/misses
        return 0.75  # Placeholder value

    def cache_function(self, ttl_hours: int = 1, tags: Optional[List[str]] = None):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(func.__name__, *args, **kwargs)

                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl_hours, tags)
                return result

            return wrapper
        return decorator


# Global cache manager
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(ttl_hours: int = 1, tags: Optional[List[str]] = None):
    """Convenience decorator for caching"""
    cache = get_cache_manager()
    return cache.cache_function(ttl_hours, tags)