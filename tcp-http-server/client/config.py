"""Client configuration and constants."""

from pathlib import Path

# Default settings
DEFAULT_DOWNLOAD_DIR = "downloads"
DEFAULT_TIMEOUT = 10.0

# Network settings
RECV_BUFFER_SIZE = 4096

# HTTP settings
HEADER_SEPARATOR = b"\r\n\r\n"

# Content types that should be printed
TEXT_CONTENT_TYPES = {"text/html", "text/plain"}

# Content types that should be saved to disk
BINARY_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/pdf",
}


# Get default download directory path
def get_default_download_dir() -> Path:
    """Get the default download directory as a Path object."""
    return Path(DEFAULT_DOWNLOAD_DIR)
