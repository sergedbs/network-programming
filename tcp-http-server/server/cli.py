"""Command-line interface - Argument parsing and application entry point."""

import sys
import argparse
import logging
from pathlib import Path
from .config import HOST, PORT, LOG_LEVELS, DEFAULT_LOG_LEVEL, ENABLE_DIR_LISTING
from .server import SimpleHTTPServer


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="server",
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
        "--dir-listing",
        type=parse_dir_listing,
        default=ENABLE_DIR_LISTING,
        metavar="enabled|disabled",
        help=f"Enable/disable directory listing (default: {'enabled' if ENABLE_DIR_LISTING else 'disabled'})",
    )

    parser.add_argument(
        "--log-level",
        choices=list(LOG_LEVELS.keys()),
        default=DEFAULT_LOG_LEVEL,
        help=f"Logging level (default: {DEFAULT_LOG_LEVEL}). "
        "Levels: debug (all), info, warning, error, none (no logs)",
    )

    return parser.parse_args()


def validate_directory(directory: str) -> Path:
    """Validate and resolve the base directory path."""
    base_dir_path = Path(directory)

    if not base_dir_path.is_absolute():
        base_dir = Path.cwd() / base_dir_path

        if not base_dir.exists() and directory == "public":
            project_root = Path(__file__).parent.parent
            base_dir = project_root / base_dir_path
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


def configure_logging(log_level: str) -> None:
    """Configure logging based on the specified level."""
    level = LOG_LEVELS.get(log_level, logging.INFO)

    if level > logging.CRITICAL:
        logging.disable(logging.CRITICAL)
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            force=True,
        )


def parse_dir_listing(value: str) -> bool:
    """Parse directory listing argument."""
    value_lower = value.lower()
    if value_lower in ("enabled", "enable", "true", "1", "yes", "on"):
        return True
    elif value_lower in ("disabled", "disable", "false", "0", "no", "off"):
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid value '{value}'. Use: enabled/disabled"
        )


def print_startup_banner(
    host: str,
    port: int,
    directory: Path,
    dir_listing: bool = ENABLE_DIR_LISTING,
    log_level: str = DEFAULT_LOG_LEVEL,
) -> None:
    """Print server startup information."""
    print("Starting HTTP server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Directory: {directory}")
    print(f"  Directory Listing: {'Enabled' if dir_listing else 'Disabled'}")
    print(f"  Log Level: {log_level}")
    print()


def main():
    """Main entry point for the HTTP server."""
    args = parse_arguments()
    validate_port(args.port)
    base_dir = validate_directory(args.directory)

    configure_logging(args.log_level)

    print_startup_banner(
        args.host, args.port, base_dir, args.dir_listing, args.log_level
    )

    try:
        server = SimpleHTTPServer(
            host=args.host,
            port=args.port,
            base_dir=str(base_dir),
            allow_directory_listing=args.dir_listing,
        )
        server.serve_forever()
    except OSError as e:
        print(f"Error: Failed to start server - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
