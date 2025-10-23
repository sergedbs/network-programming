"""
Counter test: Verify request counter works and is thread-safe.

This test makes concurrent requests to the same files and checks
if the counter increments correctly without race conditions.
"""

import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def make_request(url: str, request_id: int) -> tuple[int, int]:
    """Make a single request and return the result."""
    try:
        response = requests.get(url, timeout=10)
        return request_id, response.status_code
    except requests.RequestException as e:
        print(f"Request {request_id} failed: {e}")
        return request_id, 0


def test_counter_concurrent(base_url: str, path: str, num_requests: int = 50):
    """
    Test counter with many concurrent requests to the same file.

    If the counter is thread-safe, the final count should match
    the number of requests made.
    """
    full_url = base_url.rstrip("/") + "/" + path.lstrip("/")

    print(f"\n{'=' * 60}")
    print(f"Testing counter with {num_requests} concurrent requests")
    print(f"URL: {full_url}")
    print(f"{'=' * 60}\n")

    start_time = time.time()

    # Make concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(make_request, full_url, i)
            for i in range(1, num_requests + 1)
        ]

        success_count = 0
        for future in as_completed(futures):
            request_id, status_code = future.result()
            if status_code == 200:
                success_count += 1
            print(f"Request {request_id:3d} completed: HTTP {status_code}")

    total_time = time.time() - start_time

    print(f"\n{'=' * 60}")
    print(f"Total time: {total_time:.3f}s")
    print(f"Successful requests: {success_count}/{num_requests}")
    print(f"{'=' * 60}\n")

    # Now check the directory listing to see the counter
    print("Checking counter value...")
    print("Please open the directory listing in your browser and verify:")
    print(f"  {base_url}")
    print(f"\nThe '{path}' file should show {success_count} requests.")
    print("\nIf the number is correct, the counter is thread-safe! ✓")
    print("If it's less than expected, there's a race condition! ✗")

    return success_count


def test_counter_multiple_files(base_url: str, num_requests_per_file: int = 20):
    """
    Test counter with requests to multiple different files.

    Verifies that the counter tracks each file independently.
    """
    # Test with different paths
    paths = [
        "index.html",
        "style.css",
        "image.jpg",
    ]

    print(f"\n{'=' * 60}")
    print(f"Testing counter with {len(paths)} different files")
    print(f"{num_requests_per_file} requests per file")
    print(f"{'=' * 60}\n")

    results = {}

    for path in paths:
        full_url = base_url.rstrip("/") + "/" + path
        print(f"\nTesting: {path}")
        print("-" * 40)

        success_count = 0
        for i in range(1, num_requests_per_file + 1):
            request_id, status_code = make_request(full_url, i)
            if status_code == 200:
                success_count += 1
            time.sleep(0.05)  # Small delay to avoid rate limiting

        results[path] = success_count
        print(f"✓ {path}: {success_count}/{num_requests_per_file} successful")

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    for path, count in results.items():
        print(f"{path:20s}: {count} requests")
    print(f"{'=' * 60}\n")

    print("Please check the directory listing to verify counters match!")

    return results


def main():
    """Run counter tests."""
    SERVER_URL = "http://localhost:8080/"

    print("Request Counter Test")
    print("=" * 60)
    print("\nThis test verifies the request counter is thread-safe.")
    print("Make sure the server is running with directory listing enabled!")
    print("Start the server with: python -m server --dir-listing enabled")
    input("\nPress Enter to continue...")

    # Test 1: Many concurrent requests to same file
    print("\n### Test 1: Concurrent Requests to Same File ###")
    count = test_counter_concurrent(SERVER_URL, "index.html", num_requests=50)

    print("\nWaiting 2 seconds...")
    time.sleep(2)

    # Test 2: Requests to multiple different files
    print("\n### Test 2: Requests to Multiple Files ###")
    test_counter_multiple_files(SERVER_URL, num_requests_per_file=20)

    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print("\nOpen the browser and navigate to:")
    print(f"  {SERVER_URL}")
    print("\nVerify that the 'Requests' column shows the correct counts:")
    print(f"  - index.html should have ~{count} + 20 = {count + 20} requests")
    print("  - style.css should have ~20 requests")
    print("  - image.jpg should have ~20 requests")
    print("\nIf the counts match, the counter is thread-safe! ✓")


if __name__ == "__main__":
    main()
