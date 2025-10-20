"""HTTP protocol handling - Request parsing and response building."""

import socket
from pathlib import Path
from typing import NamedTuple
from .config import HEADER_END, MAX_HEADER_BYTES, SERVER_NAME, STATUS_TEXT
from .templates import TemplateService


class HTTPRequest(NamedTuple):
    method: str
    path: str
    version: str


def normalize_path(raw_path: str) -> str:
    """Normalize request path: strip query params, ensure leading slash, handle root."""
    # Remove query parameters
    path = raw_path.split("?", 1)[0]

    # Ensure leading slash
    if not path.startswith("/"):
        path = "/" + path

    # Default root to index.html
    if path == "/":
        path = "/index.html"

    return path


def validate_http_method(method: str, valid_methods: set[str]) -> None:
    """Validate HTTP method, raise ValueError if invalid."""
    if method.upper() not in valid_methods:
        raise ValueError(f"Unsupported HTTP method: {method}")


def validate_http_version(version: str) -> None:
    """Validate HTTP version format, raise ValueError if invalid."""
    if not version.startswith("HTTP/"):
        raise ValueError(f"Invalid HTTP version: {version}")


def format_http_headers(headers: dict, defaults: dict) -> dict:
    """Merge user headers with default headers, user headers take precedence."""
    result = dict(headers)  # Copy to avoid mutating caller's dict
    for key, value in defaults.items():
        result.setdefault(key, value)
    return result


def build_status_line(status_code: int, status_text: dict) -> str:
    """Generate HTTP/1.1 status line."""
    reason = status_text.get(status_code, "OK")
    return f"HTTP/1.1 {status_code} {reason}"


class RequestReceiver:
    """Reads request bytes until end-of-headers or size limit, then decodes."""

    def __init__(
        self, header_end: bytes = HEADER_END, max_header_bytes: int = MAX_HEADER_BYTES
    ):
        self.header_end = header_end
        self.max_header_bytes = max_header_bytes

    def receive(self, client_socket: socket.socket) -> str:
        data = bytearray()
        try:
            while self.header_end not in data:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > self.max_header_bytes:
                    raise ValueError("Request headers too large")
        except socket.timeout:
            raise ValueError("Request timed out")

        try:
            return data.decode("utf-8", errors="replace")
        except Exception:
            return ""


class RequestParser:
    """Parses the request line into an HTTPRequest."""

    VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}

    def parse(self, request_text: str) -> HTTPRequest:
        if not request_text or not request_text.strip():
            raise ValueError("Empty or invalid request")

        lines = request_text.strip().splitlines()
        if not lines:
            raise ValueError("No request line found")

        request_line = lines[0].strip()
        parts = request_line.split()
        if len(parts) != 3:
            raise ValueError(f"Invalid request line format: {request_line}")

        method, raw_path, version = parts

        # Use extracted validation functions
        validate_http_method(method, self.VALID_METHODS)
        validate_http_version(version)

        # Use extracted path normalization
        path = normalize_path(raw_path)

        return HTTPRequest(method.upper(), path, version)


class ResponseBuilder:
    """Builds HTTP responses and common error pages."""

    def __init__(
        self,
        server_name: str = SERVER_NAME,
        status_text: dict[int, str] = STATUS_TEXT,
        template_dir: Path | None = None,
    ):
        self.server_name = server_name
        self.status_text = status_text
        self.template_service = TemplateService(template_dir)

    def build(
        self, status_code: int, headers: dict, body: bytes | None = None
    ) -> bytes:
        body = body or b""

        # Merge with default headers
        defaults = {
            "Content-Length": str(len(body)),
            "Connection": "close",
            "Server": self.server_name,
        }
        merged_headers = format_http_headers(headers, defaults)

        # Build status line
        status_line = build_status_line(status_code, self.status_text)

        # Build header lines
        lines = [status_line]
        for k, v in merged_headers.items():
            lines.append(f"{k}: {v}")
        lines.append("")  # end of headers

        head = "\r\n".join(lines).encode("utf-8", errors="strict") + b"\r\n"
        return head + body

    @staticmethod
    def html_error_body(title: str, heading: str) -> bytes:
        return (
            f"<html><head><title>{title}</title></head>"
            f"<body><h1>{heading}</h1></body></html>"
        ).encode("utf-8")

    def html(
        self, status_code: int, body: bytes, extra_headers: dict | None = None
    ) -> bytes:
        headers = {"Content-Type": "text/html; charset=utf-8"}
        if extra_headers:
            headers.update(extra_headers)
        return self.build(status_code, headers, body)

    def _render_html_response(
        self, status_code: int, html: str, extra_headers: dict | None = None
    ) -> bytes:
        """Helper to build HTML response from template string."""
        headers = {"Content-Type": "text/html; charset=utf-8"}
        if extra_headers:
            headers.update(extra_headers)
        return self.build(status_code, headers, html.encode("utf-8"))

    def error(
        self,
        status_code: int,
        message: str | None = None,
        allow_header: str | None = None,
    ) -> bytes:
        """Generate standard HTML error response for given status code using templates."""
        reason = self.status_text.get(status_code, "Error")

        html = self.template_service.render_error(
            status_code=status_code,
            status_text=reason if message is None else message,
            message=reason if message is None else message,
            server_name=self.server_name,
        )

        extra_headers = {"Allow": allow_header} if allow_header else None
        return self._render_html_response(status_code, html, extra_headers)

    def directory_listing(self, path: str, entries: list[dict]) -> bytes:
        """Generate directory listing HTML response using templates."""
        html = self.template_service.render_directory(
            path=path, entries=entries, server_name=self.server_name
        )

        return self._render_html_response(200, html)
