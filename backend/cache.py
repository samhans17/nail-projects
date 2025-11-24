# backend/cache.py
import hashlib
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import threading


@dataclass
class CacheEntry:
    """Cache entry with data and timestamp"""
    data: Any
    timestamp: float
    image_hash: str


class SegmentationCache:
    """Thread-safe LRU cache for segmentation results"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live in seconds (default 5 minutes)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._access_order = []  # Track access order for LRU

    def _compute_hash(self, image_bytes: bytes) -> str:
        """Compute hash of image bytes for cache key"""
        return hashlib.md5(image_bytes).hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry has expired"""
        return (time.time() - entry.timestamp) > self.ttl_seconds

    def _evict_lru(self):
        """Evict least recently used entry"""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            self._cache.pop(lru_key, None)

    def get(self, image_bytes: bytes) -> Optional[Any]:
        """
        Get cached segmentation result

        Args:
            image_bytes: Raw image bytes

        Returns:
            Cached data if exists and valid, None otherwise
        """
        cache_key = self._compute_hash(image_bytes)

        with self._lock:
            entry = self._cache.get(cache_key)

            if entry is None:
                return None

            # Check if expired
            if self._is_expired(entry):
                self._cache.pop(cache_key)
                self._access_order.remove(cache_key)
                return None

            # Update access order (move to end for LRU)
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)

            return entry.data

    def set(self, image_bytes: bytes, data: Any):
        """
        Store segmentation result in cache

        Args:
            image_bytes: Raw image bytes
            data: Segmentation result data
        """
        cache_key = self._compute_hash(image_bytes)

        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_lru()

            # Store entry
            entry = CacheEntry(
                data=data,
                timestamp=time.time(),
                image_hash=cache_key
            )
            self._cache[cache_key] = entry

            # Update access order
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "entries": [
                    {
                        "hash": entry.image_hash[:8],
                        "age_seconds": time.time() - entry.timestamp
                    }
                    for entry in self._cache.values()
                ]
            }


# Global cache instance
segmentation_cache = SegmentationCache(max_size=100, ttl_seconds=300)
