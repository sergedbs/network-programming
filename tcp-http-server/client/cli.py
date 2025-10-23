"""Command-line interface - Argument parsing and URL handling."""

import sys
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

from .config import DEFAULT_TIMEOUT, get_default_download_dir


class ClientArgs(NamedTuple):
    """Parsed command-line arguments."""

    host: str
    port: int
    path: str
    directory: Path
    timeout: float


def print_usage() -> None:
    """Print usage instructions."""
    print("Usage:")
    print("  python -m client <url> [directory]")
    print("  python -m client <host> <port> <path> [directory]")
    print()
    print("Arguments:")
    print("  url           Full URL (e.g., http://localhost:8080/index.html)")
    print("  host          Server hostname or IP address (e.g., localhost)")
    print("  port          Server port number (e.g., 8080)")
    print("  path          URL path to request (e.g., /index.html or /)")
    print(
        f"  directory     Directory to save files (default: {get_default_download_dir()})"
    )
    print()
    print("Examples:")
    print("  python -m client http://localhost:8080/image.jpg")
    print("  python -m client http://localhost:8080/Cat.pdf downloads")
    print("  python -m client localhost 8080 / downloads")
    print("  python -m client 127.0.0.1 8080 /index.html")
    print("  python -m client localhost 8080 /subdir/ downloads")


def parse_url(url: str) -> tuple[str, int, str]:
    """
    Parse URL into host, port, and path.

    Args:
        url: URL string (e.g., "http://localhost:8080/index.html")

    Returns:
        Tuple of (host, port, path)

    Raises:
        ValueError: If URL is invalid
    """
    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)

    # Extract host
    host = parsed.hostname
    if not host:
        raise ValueError("Invalid URL: missing hostname")

    # Extract port (default to 80 if not specified)
    port = parsed.port if parsed.port else 80

    # Extract path (default to / if empty)
    path = parsed.path if parsed.path else "/"

    return host, port, path


def parse_arguments(args: list[str]) -> ClientArgs:
    """
    Parse and validate command-line arguments.

    Args:
        args: Command-line arguments (excluding script name)

    Returns:
        ClientArgs object with parsed values

    Raises:
        ValueError: If arguments are invalid
    """
    if len(args) == 0:
        raise ValueError("No arguments provided")

    # Case 1: URL format (1 or 2 arguments)
    # python -m client <url> [directory]
    if len(args) <= 2 and "/" in args[0]:
        url = args[0]
        directory = args[1] if len(args) == 2 else str(get_default_download_dir())

        try:
            host, port, path = parse_url(url)
        except ValueError as e:
            raise ValueError(f"Invalid URL: {e}")

        return ClientArgs(
            host=host,
            port=port,
            path=path,
            directory=Path(directory),
            timeout=DEFAULT_TIMEOUT,
        )

    # Case 2: Separate arguments format (3 or 4 arguments)
    # python -m client <host> <port> <path> [directory]
    if len(args) in (3, 4):
        host = args[0]
        port_str = args[1]
        path = args[2]
        directory = args[3] if len(args) == 4 else str(get_default_download_dir())

        # Validate host
        if not host:
            raise ValueError("Server host cannot be empty")

        # Validate and parse port
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                raise ValueError(f"Port must be between 1 and 65535, got {port}")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Port must be a number, got '{port_str}'")
            raise

        # Validate URL path
        if not path:
            raise ValueError("URL path cannot be empty")

        return ClientArgs(
            host=host,
            port=port,
            path=path,
            directory=Path(directory),
            timeout=DEFAULT_TIMEOUT,
        )

    # Invalid number of arguments
    raise ValueError(f"Invalid number of arguments: {len(args)}")


def main() -> None:
    """Main CLI entry point."""
    # Import here to avoid circular imports
    from .client import run_client

    # Get command-line arguments (excluding script name)
    args = sys.argv[1:]

    # Check for help flag
    if "-h" in args or "--help" in args or len(args) == 0:
        print_usage()
        sys.exit(0 if len(args) > 0 else 1)

    # Parse arguments
    try:
        client_args = parse_arguments(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(file=sys.stderr)
        print_usage()
        sys.exit(1)

    # Run client
    run_client(client_args)
