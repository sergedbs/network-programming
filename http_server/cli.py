"""Command-line interface - Argument parsing and application entry point."""

import sys
import argparse
from pathlib import Path
from .config import HOST, PORT
from .server import SimpleHTTPServer


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Simple HTTP Server - Serve static files over HTTP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Serve 'public' directory on 0.0.0.0:8080
  %(prog)s -d /var/www              # Serve /var/www directory
  %(prog)s -p 3000                  # Use port 3000
  %(prog)s -d ./dist -p 8000        # Serve ./dist on port 8000
  %(prog)s --host 127.0.0.1         # Listen only on localhost
        """,
    )

    parser.add_argument(
        "-d",
        "--dir",
        "--directory",
        dest="directory",
        default="public",
        help="Directory to serve (default: public)",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=PORT,
        help=f"Port to listen on (default: {PORT}, range: 1-65535)",
    )

    parser.add_argument(
        "--host",
        default=HOST,
        help=f"Host/IP to bind to (default: {HOST})",
    )

    parser.add_argument(
        "--enable-dir-listing",
        action="store_true",
        help="Enable directory listing (default: disabled)",
    )

    return parser.parse_args()


def validate_directory(directory: str) -> Path:
    """Validate and resolve the base directory path."""
    base_dir_path = Path(directory)

    if not base_dir_path.is_absolute():
        # For relative paths, first try relative to current directory
        base_dir = Path.cwd() / base_dir_path

        # If not found and using default "public", try relative to script location
        if not base_dir.exists() and directory == "public":
            script_dir = Path(__file__).parent
            base_dir = script_dir / base_dir_path
    else:
        base_dir = base_dir_path

    base_dir = base_dir.resolve()

    if not base_dir.exists():
        print(f"Error: Directory '{directory}' does not exist", file=sys.stderr)
        print(f"Looked for: {base_dir}", file=sys.stderr)
        sys.exit(1)

    if not base_dir.is_dir():
        print(f"Error: '{directory}' is not a directory", file=sys.stderr)
        sys.exit(1)

    try:
        list(base_dir.iterdir())
    except PermissionError:
        print(
            f"Error: Permission denied to read directory '{directory}'",
            file=sys.stderr,
        )
        sys.exit(1)

    return base_dir


def validate_port(port: int) -> None:
    """Validate that port is in valid range."""
    if not (1 <= port <= 65535):
        print(f"Error: Port must be between 1 and 65535, got {port}", file=sys.stderr)
        sys.exit(1)


def print_startup_banner(
    host: str, port: int, directory: Path, dir_listing: bool = False
) -> None:
    """Print server startup information."""
    print("Starting HTTP server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Directory: {directory}")
    print(f"  Directory Listing: {'Enabled' if dir_listing else 'Disabled'}")
    print()


def main():
    """Main entry point for the HTTP server."""
    args = parse_arguments()
    validate_port(args.port)
    base_dir = validate_directory(args.directory)
    print_startup_banner(args.host, args.port, base_dir, args.enable_dir_listing)

    try:
        server = SimpleHTTPServer(
            host=args.host,
            port=args.port,
            base_dir=str(base_dir),
            allow_directory_listing=args.enable_dir_listing,
        )
        server.serve_forever()
    except OSError as e:
        print(f"Error: Failed to start server - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
