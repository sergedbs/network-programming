"""Thread-safe rate limiter for controlling requests per IP address."""

import threading
import time
from collections import defaultdict, deque
from .config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window algorithm.

    Tracks request timestamps per IP and allows a maximum number of requests
    within a time window.
    """

    def __init__(
        self,
        max_requests: int = RATE_LIMIT_REQUESTS,
        window_seconds: float = RATE_LIMIT_WINDOW,
    ):
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(deque)  # IP -> deque of timestamps
        self._lock = threading.Lock()

    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if a request from the given IP is allowed.

        This method also records the request timestamp if allowed.

        Args:
            client_ip: The IP address of the client

        Returns:
            True if the request is allowed, False if rate limit exceeded
        """
        current_time = time.time()

        with self._lock:
            # Get the request history for this IP
            request_times = self._requests[client_ip]

            # Remove timestamps outside the current window
            cutoff_time = current_time - self.window_seconds
            while request_times and request_times[0] < cutoff_time:
                request_times.popleft()

            # Check if we're under the limit
            if len(request_times) < self.max_requests:
                request_times.append(current_time)
                return True

            return False

    def get_request_count(self, client_ip: str) -> int:
        """
        Get the number of requests in the current window for an IP.

        Args:
            client_ip: The IP address to check

        Returns:
            Number of requests in the current window
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        with self._lock:
            request_times = self._requests[client_ip]
            # Count requests within the window
            return sum(1 for t in request_times if t >= cutoff_time)
