"""Response handlers - Handle different content types."""

from pathlib import Path

from .config import BINARY_CONTENT_TYPES, TEXT_CONTENT_TYPES
from .http_protocol import HTTPResponse


def get_content_type(headers: dict[str, str]) -> str:
    """Extract content type from headers (case-insensitive)."""
    for key, value in headers.items():
        if key.lower() == "content-type":
            # Return main type, ignore charset parameters
            return value.split(";")[0].strip().lower()
    return "application/octet-stream"


def get_filename_from_path(url_path: str) -> str:
    """Extract filename from URL path."""
    path = Path(url_path)
    if path.name:
        return path.name
    return "index.html"


def save_file(body: bytes, directory: Path, filename: str) -> Path:
    """
    Save file to directory.

    Args:
        body: File content as bytes
        directory: Directory to save to
        filename: Name of file to save

    Returns:
        Path to saved file
    """
    # Create directory if it doesn't exist
    directory.mkdir(parents=True, exist_ok=True)

    # Handle duplicate filenames
    filepath = directory / filename
    if filepath.exists():
        # Add number suffix if file exists
        stem = filepath.stem
        suffix = filepath.suffix
        counter = 1
        while filepath.exists():
            filepath = directory / f"{stem}_{counter}{suffix}"
            counter += 1

    # Write file
    filepath.write_bytes(body)
    return filepath


class ResponseHandler:
    """Handles HTTP responses based on content type."""

    def __init__(self, save_directory: Path):
        """
        Initialize response handler.

        Args:
            save_directory: Directory to save files to
        """
        self.save_directory = save_directory

    def handle(self, response: HTTPResponse, url_path: str) -> None:
        """
        Handle HTTP response based on content type.

        Args:
            response: HTTPResponse object
            url_path: Original URL path requested
        """
        if response.status_code != 200:
            self._handle_error(response)
            return

        content_type = get_content_type(response.headers)

        if content_type in TEXT_CONTENT_TYPES:
            self._handle_text(response)
        elif content_type in BINARY_CONTENT_TYPES:
            self._handle_binary(response, url_path)
        else:
            self._handle_unknown(response, url_path)

    def _handle_error(self, response: HTTPResponse) -> None:
        """Handle error responses."""
        print(f"Error: HTTP {response.status_code} {response.status_text}")
        if response.body:
            try:
                print(response.body.decode("utf-8", errors="replace"))
            except Exception:
                print("(Unable to decode error response)")

    def _handle_text(self, response: HTTPResponse) -> None:
        """Handle text/HTML responses by printing them."""
        try:
            text = response.body.decode("utf-8", errors="replace")
            print(text)
        except Exception as e:
            print(f"Error decoding response: {e}")

    def _handle_binary(self, response: HTTPResponse, url_path: str) -> None:
        """Handle binary files by saving them."""
        filename = get_filename_from_path(url_path)
        try:
            filepath = save_file(response.body, self.save_directory, filename)
            print(f"File saved: {filepath}")
        except Exception as e:
            print(f"Error saving file: {e}")

    def _handle_unknown(self, response: HTTPResponse, url_path: str) -> None:
        """Handle unknown content types."""
        content_type = get_content_type(response.headers)
        print(f"Received content type: {content_type}")
        print(f"Body size: {len(response.body)} bytes")

        # Try to print as text, otherwise save as binary
        try:
            text = response.body.decode("utf-8", errors="strict")
            print(text)
        except UnicodeDecodeError:
            filename = get_filename_from_path(url_path)
            filepath = save_file(response.body, self.save_directory, filename)
            print(f"Binary file saved: {filepath}")
