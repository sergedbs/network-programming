"""HTTP protocol handling - Client requests and response parsing."""

import socket
from typing import NamedTuple

from .config import HEADER_SEPARATOR, RECV_BUFFER_SIZE


class HTTPResponse(NamedTuple):
    """Represents a parsed HTTP response."""

    status_code: int
    status_text: str
    headers: dict[str, str]
    body: bytes


class HTTPClient:
    """Simple HTTP/1.1 client for making GET requests."""

    def __init__(self, host: str, port: int, timeout: float):
        """
        Initialize HTTP client.

        Args:
            host: Server hostname or IP address
            port: Server port number
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout

    def get(self, path: str) -> HTTPResponse:
        """
        Send HTTP GET request and return parsed response.

        Args:
            path: URL path (e.g., '/index.html' or '/subdir/file.pdf')

        Returns:
            HTTPResponse object with status, headers, and body

        Raises:
            ConnectionError: If connection fails
            ValueError: If response is malformed
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        # Build HTTP request
        request = self._build_request(path)

        # Connect and send request
        try:
            response_data = self._send_request(request)
        except socket.timeout:
            raise ConnectionError(f"Connection to {self.host}:{self.port} timed out")
        except socket.error as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")

        # Parse response
        return parse_response(response_data)

    def _build_request(self, path: str) -> bytes:
        """Build HTTP GET request."""
        request = (
            f"GET {path} HTTP/1.1\r\nHost: {self.host}\r\nConnection: close\r\n\r\n"
        )
        return request.encode("utf-8")

    def _send_request(self, request: bytes) -> bytes:
        """Send request and receive response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            sock.sendall(request)
            return self._receive_full_response(sock)

    def _receive_full_response(self, sock: socket.socket) -> bytes:
        """Receive complete HTTP response from socket."""
        data = bytearray()
        while True:
            chunk = sock.recv(RECV_BUFFER_SIZE)
            if not chunk:
                break
            data.extend(chunk)
        return bytes(data)


def parse_response(data: bytes) -> HTTPResponse:
    """
    Parse HTTP response into status, headers, and body.

    Args:
        data: Raw response bytes

    Returns:
        HTTPResponse object

    Raises:
        ValueError: If response format is invalid
    """
    # Split headers from body
    if HEADER_SEPARATOR not in data:
        raise ValueError("Invalid HTTP response: no header/body separator found")

    header_section, body = data.split(HEADER_SEPARATOR, 1)

    # Decode headers
    try:
        header_text = header_section.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Invalid HTTP response: headers not UTF-8")

    lines = header_text.strip().split("\r\n")
    if not lines:
        raise ValueError("Invalid HTTP response: empty headers")

    # Parse status line
    status_code, status_text = parse_status_line(lines[0])

    # Parse headers
    headers = parse_headers(lines[1:])

    return HTTPResponse(
        status_code=status_code, status_text=status_text, headers=headers, body=body
    )


def parse_status_line(status_line: str) -> tuple[int, str]:
    """
    Parse HTTP status line.

    Args:
        status_line: Status line string (e.g., "HTTP/1.1 200 OK")

    Returns:
        Tuple of (status_code, status_text)

    Raises:
        ValueError: If status line format is invalid
    """
    parts = status_line.split(" ", 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid status line: {status_line}")

    version, status_code_str, status_text = parts
    if not version.startswith("HTTP/"):
        raise ValueError(f"Invalid HTTP version: {version}")

    try:
        status_code = int(status_code_str)
    except ValueError:
        raise ValueError(f"Invalid status code: {status_code_str}")

    return status_code, status_text


def parse_headers(header_lines: list[str]) -> dict[str, str]:
    """
    Parse HTTP headers.

    Args:
        header_lines: List of header lines

    Returns:
        Dictionary of header key-value pairs
    """
    headers = {}
    for line in header_lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers
