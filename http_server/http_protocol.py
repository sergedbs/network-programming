"""HTTP protocol handling - Request parsing and response building."""

import socket
from typing import NamedTuple
from .config import HEADER_END, MAX_HEADER_BYTES, SERVER_NAME, STATUS_TEXT


class HTTPRequest(NamedTuple):
    method: str
    path: str
    version: str


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

        if method.upper() not in self.VALID_METHODS:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if not version.startswith("HTTP/"):
            raise ValueError(f"Invalid HTTP version: {version}")

        path = raw_path.split("?", 1)[0]
        if not path.startswith("/"):
            path = "/" + path
        if path == "/":
            path = "/index.html"

        return HTTPRequest(method.upper(), path, version)


class ResponseBuilder:
    """Builds HTTP responses and common error pages."""

    def __init__(
        self, server_name: str = SERVER_NAME, status_text: dict[int, str] = STATUS_TEXT
    ):
        self.server_name = server_name
        self.status_text = status_text

    def build(
        self, status_code: int, headers: dict, body: bytes | None = None
    ) -> bytes:
        reason = self.status_text.get(status_code, "OK")
        body = body or b""
        headers = dict(headers)  # copy to avoid mutating callers
        headers.setdefault("Content-Length", str(len(body)))
        headers.setdefault("Connection", "close")
        headers.setdefault("Server", self.server_name)

        lines = [f"HTTP/1.1 {status_code} {reason}"]
        for k, v in headers.items():
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

    def error(self, status_code: int, allow_header: str | None = None) -> bytes:
        """Generate standard HTML error response for given status code."""
        reason = self.status_text.get(status_code, "Error")
        title = f"{status_code} {reason}"
        body = self.html_error_body(title, title)
        headers = {"Content-Type": "text/html; charset=utf-8"}
        if allow_header:
            headers["Allow"] = allow_header
        return self.build(status_code, headers, body)
