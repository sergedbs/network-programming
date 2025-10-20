import socket
from pathlib import Path
import mimetypes
from typing import NamedTuple

HOST = "0.0.0.0"
PORT = 8080

STATUS_TEXT = {
    200: "OK",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}

BACKLOG = 100
CLIENT_TIMEOUT_SECONDS = 5
HEADER_END = b"\r\n\r\n"
MAX_HEADER_BYTES = 64 * 1024
SERVER_NAME = "SimplePythonSocketHTTP/1.0"


class HTTPRequest(NamedTuple):
    method: str
    path: str
    version: str


def create_socket(host: str, port: int) -> socket.socket:
    """Create, bind, and listen on a TCP socket."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(BACKLOG)
    server.setblocking(True)
    return server


def accept_connection(server: socket.socket) -> tuple[socket.socket, tuple[str, int]]:
    """Accept a client connection and set a read timeout."""
    client_socket, client_address = server.accept()
    client_socket.settimeout(CLIENT_TIMEOUT_SECONDS)
    return client_socket, client_address


def receive_http_request(client_socket: socket.socket) -> str:
    """Read bytes until end-of-headers or a limit, then decode to text."""
    data = bytearray()
    try:
        while HEADER_END not in data:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > MAX_HEADER_BYTES:
                raise ValueError("Request headers too large")
    except socket.timeout:
        raise ValueError("Request timed out")

    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def parse_request(request_text: str) -> HTTPRequest:
    """Parse the request line and return HTTPRequest(method, path, version)."""
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

    valid_methods = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}
    if method.upper() not in valid_methods:
        raise ValueError(f"Unsupported HTTP method: {method}")

    if not version.startswith("HTTP/"):
        raise ValueError(f"Invalid HTTP version: {version}")

    path = raw_path.split("?", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    if path == "/":
        path = "/index.html"

    return HTTPRequest(method.upper(), path, version)


def get_file_path(
    request_path: str, base_dir: str = "public", allow_directory: bool = True
) -> Path | None:
    relative = request_path.lstrip("/")
    base = Path(base_dir).resolve()
    target = (base / relative).resolve()

    try:
        target.relative_to(base)
    except ValueError:
        return None

    if not target.exists():
        return None

    if target.is_file():
        return target

    if allow_directory and target.is_dir():
        return target

    return None


def determine_content_type(file_path: str | Path) -> str:
    file_path = str(file_path)
    mimetype, _ = mimetypes.guess_type(file_path)
    if mimetype is None:
        return "application/octet-stream"

    return mimetype


def build_http_response(status_code: int, headers: dict, body: bytes) -> bytes:
    """Assemble an HTTP/1.1 response with standard defaults."""
    reason = STATUS_TEXT.get(status_code, "OK")
    if body is None:
        body = b""
    if "Content-Length" not in headers:
        headers["Content-Length"] = str(len(body))
    if "Connection" not in headers:
        headers["Connection"] = "close"
    if "Server" not in headers:
        headers["Server"] = SERVER_NAME

    lines = [f"HTTP/1.1 {status_code} {reason}"]
    for k, v in headers.items():
        lines.append(f"{k}: {v}")
    lines.append("")
    head = "\r\n".join(lines).encode("utf-8", errors="strict") + b"\r\n"
    return head + body


def html_error_body(title: str, heading: str) -> bytes:
    return (
        f"<html><head><title>{title}</title></head>"
        f"<body><h1>{heading}</h1></body></html>"
    ).encode("utf-8")


def generate_html_response(
    status_code: int, body: bytes, extra_headers: dict | None = None
) -> bytes:
    headers = {"Content-Type": "text/html; charset=utf-8"}
    if extra_headers:
        headers.update(extra_headers)
    return build_http_response(status_code, headers, body)


def generate_404_response() -> bytes:
    return generate_html_response(
        404, html_error_body("404 Not Found", "404 Not Found")
    )


def generate_403_response() -> bytes:
    return generate_html_response(
        403, html_error_body("403 Forbidden", "403 Forbidden")
    )


def generate_500_response() -> bytes:
    return generate_html_response(
        500, html_error_body("500 Internal Server Error", "500 Internal Server Error")
    )


def generate_405_response() -> bytes:
    return generate_html_response(
        405,
        html_error_body("405 Method Not Allowed", "405 Method Not Allowed"),
        {"Allow": "GET, HEAD"},
    )


def generate_400_response() -> bytes:
    return generate_html_response(
        400, html_error_body("400 Bad Request", "400 Bad Request")
    )


def handle_client(client_socket, base_dir: str = "public") -> None:
    """Handle a single request/response lifecycle for a client socket."""
    try:
        request_text = receive_http_request(client_socket)
        req = parse_request(request_text)

        if req.method not in {"GET", "HEAD"}:
            client_socket.sendall(generate_405_response())
            return

        target = get_file_path(req.path, base_dir=base_dir, allow_directory=False)
        if not target or not Path(target).is_file():
            client_socket.sendall(generate_404_response())
            return

        data = Path(target).read_bytes()
        content_type = determine_content_type(target)

        headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
            "Connection": "close",
        }

        body = b"" if req.method == "HEAD" else data
        client_socket.sendall(build_http_response(200, headers, body))

    except ValueError:
        client_socket.sendall(generate_400_response())
    except Exception:
        client_socket.sendall(generate_500_response())
    finally:
        try:
            client_socket.close()
        except Exception:
            pass


def start_server():
    server = create_socket(HOST, PORT)
    while True:
        client_socket, addr = accept_connection(server)
        handle_client(client_socket, base_dir="public")


def main():
    start_server()


if __name__ == "__main__":
    main()
