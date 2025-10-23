"""Thread-safe request counter for tracking requests per file path."""

import threading
from collections import defaultdict


class RequestCounter:
    """Thread-safe counter for tracking requests to each file path."""

    def __init__(self):
        self._counts = defaultdict(int)
        self._lock = threading.Lock()

    def increment(self, path: str) -> int:
        """
        Increment the counter for the given path.

        Returns:
            The new count for this path.
        """
        with self._lock:
            self._counts[path] += 1
            return self._counts[path]

    def get(self, path: str) -> int:
        """
        Get the current count for the given path.

        Returns:
            The count for this path, or 0 if never accessed.
        """
        with self._lock:
            return self._counts[path]

    def get_all(self) -> dict[str, int]:
        """
        Get a snapshot of all counts.

        Returns:
            A dictionary of path -> count mappings.
        """
        with self._lock:
            return dict(self._counts)
