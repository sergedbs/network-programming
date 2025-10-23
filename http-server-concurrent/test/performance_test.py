"""
Performance test: Compare single-threaded vs concurrent server.

This script sends multiple concurrent requests to test the server's
ability to handle them in parallel.
"""

import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def make_request(url: str, request_id: int) -> tuple[int, float, int]:
    """
    Make a single HTTP request.

    Returns:
        Tuple of (request_id, duration, status_code)
    """
    start = time.time()
    try:
        response = requests.get(url, timeout=30)
        duration = time.time() - start
        return request_id, duration, response.status_code
    except requests.RequestException as e:
        duration = time.time() - start
        print(f"Request {request_id} failed: {e}")
        return request_id, duration, 0


def test_concurrent_requests(url: str, num_requests: int = 10, max_workers: int = 10):
    """Test server with concurrent requests."""
    print(f"\n{'=' * 60}")
    print(f"Testing {num_requests} concurrent requests to {url}")
    print(f"Using {max_workers} worker threads")
    print(f"{'=' * 60}\n")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(make_request, url, i) for i in range(1, num_requests + 1)
        ]

        results = []
        for future in as_completed(futures):
            request_id, duration, status_code = future.result()
            results.append((request_id, duration, status_code))
            print(
                f"✓ Request {request_id:2d} completed in {duration:.3f}s (HTTP {status_code})"
            )

    total_time = time.time() - start_time

    # Calculate statistics
    successful = sum(1 for _, _, status in results if 200 <= status < 300)
    avg_time = sum(d for _, d, _ in results) / len(results) if results else 0

    print(f"\n{'=' * 60}")
    print(f"Total time: {total_time:.3f}s")
    print(f"Successful requests: {successful}/{num_requests}")
    print(f"Average request time: {avg_time:.3f}s")
    print(f"Throughput: {num_requests / total_time:.2f} requests/second")
    print(f"{'=' * 60}\n")

    return total_time, successful


def main():
    """Run performance tests."""
    # Configuration
    SERVER_URL = "http://localhost:8080/"
    NUM_REQUESTS = 10

    print("Concurrent HTTP Server Performance Test")
    print("=" * 60)
    print("\nMake sure the server is running before proceeding!")
    print("Start the server with: python -m server")
    input("\nPress Enter to continue...")

    # Test 1: Concurrent requests
    print("\n### Test 1: Concurrent Requests ###")
    total_time, successful = test_concurrent_requests(SERVER_URL, NUM_REQUESTS, 10)

    print("\n### Analysis ###")
    print("If the server handles requests concurrently, the total time")
    print("should be close to the time of a single request (~1s if delayed).")
    print(f"If sequential, it would take ~{NUM_REQUESTS}s.")
    print(f"\nActual time: {total_time:.3f}s")

    if total_time < NUM_REQUESTS * 0.5:  # Much faster than sequential
        print("✓ Server is handling requests CONCURRENTLY!")
    else:
        print("⚠ Server might be handling requests sequentially")


if __name__ == "__main__":
    main()
