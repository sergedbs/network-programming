"""
Rate limiting test: Verify rate limiter works correctly.

Tests the server's rate limiting by making requests at different rates
from simulated different IPs (using headers if supported, or manually).
"""

import time
import requests


def make_request_with_delay(
    url: str, request_id: int, delay: float = 0
) -> tuple[int, int, float]:
    """Make a request after a delay."""
    if delay > 0:
        time.sleep(delay)

    start = time.time()
    try:
        response = requests.get(url, timeout=10)
        duration = time.time() - start
        return request_id, response.status_code, duration
    except requests.RequestException:
        duration = time.time() - start
        return request_id, 0, duration


def test_rate_limit_spam(url: str, num_requests: int = 20):
    """
    Test rate limiting by spamming requests as fast as possible.

    Expected: First 5 requests succeed (200), rest are rate limited (429).
    """
    print(f"\n{'=' * 60}")
    print("Test: Spamming requests (exceeding rate limit)")
    print(f"{'=' * 60}\n")

    results = []
    for i in range(1, num_requests + 1):
        request_id, status_code, duration = make_request_with_delay(url, i, delay=0)
        results.append((request_id, status_code, duration))

        status_symbol = "✓" if status_code == 200 else "✗"
        status_text = f"HTTP {status_code}" if status_code else "ERROR"
        print(
            f"{status_symbol} Request {request_id:2d}: {status_text} ({duration:.3f}s)"
        )

        # Small delay to avoid overwhelming the connection
        time.sleep(0.05)

    # Analyze results
    success_count = sum(1 for _, status, _ in results if status == 200)
    rate_limited_count = sum(1 for _, status, _ in results if status == 429)

    print(f"\n{'=' * 60}")
    print(f"Successful (200): {success_count}/{num_requests}")
    print(f"Rate limited (429): {rate_limited_count}/{num_requests}")
    print(f"{'=' * 60}\n")

    return success_count, rate_limited_count


def test_rate_limit_under_limit(url: str, num_requests: int = 10, delay: float = 0.25):
    """
    Test by staying under the rate limit.

    Expected: All requests succeed (200).
    """
    print(f"\n{'=' * 60}")
    print(f"Test: Sending requests with {delay}s delay (under rate limit)")
    print(f"{'=' * 60}\n")

    results = []
    for i in range(1, num_requests + 1):
        request_id, status_code, duration = make_request_with_delay(url, i, delay)
        results.append((request_id, status_code, duration))

        status_symbol = "✓" if status_code == 200 else "✗"
        status_text = f"HTTP {status_code}" if status_code else "ERROR"
        print(
            f"{status_symbol} Request {request_id:2d}: {status_text} ({duration:.3f}s)"
        )

    # Analyze results
    success_count = sum(1 for _, status, _ in results if status == 200)
    rate_limited_count = sum(1 for _, status, _ in results if status == 429)

    print(f"\n{'=' * 60}")
    print(f"Successful (200): {success_count}/{num_requests}")
    print(f"Rate limited (429): {rate_limited_count}/{num_requests}")
    print(f"{'=' * 60}\n")

    return success_count, rate_limited_count


def main():
    """Run rate limiting tests."""
    SERVER_URL = "http://localhost:8080/"

    print("Rate Limiting Test")
    print("=" * 60)
    print("\nDefault rate limit: 5 requests per second per IP")
    print("Make sure the server is running before proceeding!")
    print("Start the server with: python -m server")
    input("\nPress Enter to continue...")

    # Test 1: Spam requests (exceed rate limit)
    print("\n### Test 1: Exceeding Rate Limit ###")
    success1, limited1 = test_rate_limit_spam(SERVER_URL, num_requests=20)

    print("\n⏳ Waiting 2 seconds before next test...")
    time.sleep(2)

    # Test 2: Stay under rate limit
    print("\n### Test 2: Staying Under Rate Limit ###")
    success2, limited2 = test_rate_limit_under_limit(
        SERVER_URL, num_requests=10, delay=0.25
    )

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nTest 1 (Spam): {success1} successful, {limited1} rate limited")
    print(f"Test 2 (Under limit): {success2} successful, {limited2} rate limited")

    if limited1 > 0 and limited2 == 0:
        print("\n✓ Rate limiter is working correctly! 🎉")
    elif limited1 > 0:
        print("\n⚠ Rate limiter is working but might be too aggressive")
    else:
        print("\n✗ Rate limiter might not be working properly")


if __name__ == "__main__":
    main()
