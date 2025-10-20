import socket
from pathlib import Path
import mimetypes

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


def create_socket(host: str, port: int) -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    server.setblocking(True)
    return server


def accept_connection(server: socket.socket) -> tuple[socket.socket, tuple[str, int]]:
    client_socket, client_address = server.accept()
    client_socket.settimeout(5)
    return client_socket, client_address


def receive_http_request(client_socket: socket.socket) -> str:
    HEADER_END = b"\r\n\r\n"
    MAX_HEADER_BYTES = 64 * 1024
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
        request_text = data.decode("utf-8", errors="replace")
    except Exception:
        request_text = ""

    return request_text


def parse_request(request_text: str):
    """Parse HTTP request and return method, path, version with validation."""

    if not request_text or not request_text.strip():
        raise ValueError("Empty or invalid request")

    lines = request_text.strip().splitlines()
    if not lines:
        raise ValueError("No request line found")

    # Parse request line
    request_line = lines[0].strip()
    parts = request_line.split()

    if len(parts) != 3:
        raise ValueError(f"Invalid request line format: {request_line}")

    method, raw_path, version = parts

    # Validate HTTP method
    valid_methods = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}
    if method.upper() not in valid_methods:
        raise ValueError(f"Unsupported HTTP method: {method}")

    # Validate HTTP version
    if not version.startswith("HTTP/"):
        raise ValueError(f"Invalid HTTP version: {version}")

    # Parse path and remove query string
    path = raw_path
    query_pos = path.find("?")
    if query_pos != -1:
        path = path[:query_pos]

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Default to index.html for root path
    if path == "/":
        path = "/index.html"

    return method.upper(), path, version


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
    reason = STATUS_TEXT.get(status_code, "OK")

    if body is None:
        body = b""
    if "Content-Length" not in headers:
        headers["Content-Length"] = str(len(body))
    if "Connection" not in headers:
        headers["Connection"] = "close"
    if "Server" not in headers:
        headers["Server"] = "SimplePythonSocketHTTP/1.0"

    lines = [f"HTTP/1.1 {status_code} {reason}"]
    for k, v in headers.items():
        lines.append(f"{k}: {v}")
    lines.append("")

    head = "\r\n".join(lines).encode("utf-8", errors="strict") + b"\r\n"
    return head + body


def generate_404_response() -> bytes:
    body = (
        b"<html><head><title>404 Not Found</title></head>"
        b"<body><h1>404 Not Found</h1></body></html>"
    )

    headers = {
        "Content-Type": "text/html; charset=utf-8",
    }
    return build_http_response(404, headers, body)


def generate_403_response() -> bytes:
    body = (
        b"<html><head><title>403 Forbidden</title></head>"
        b"<body><h1>403 Forbidden</h1></body></html>"
    )

    headers = {
        "Content-Type": "text/html; charset=utf-8",
    }
    return build_http_response(403, headers, body)


def generate_500_response() -> bytes:
    body = (
        b"<html><head><title>500 Internal Server Error</title></head>"
        b"<body><h1>500 Internal Server Error</h1></body></html>"
    )

    headers = {
        "Content-Type": "text/html; charset=utf-8",
    }
    return build_http_response(500, headers, body)


def generate_405_response() -> bytes:
    body = (
        b"<html><head><title>405 Method Not Allowed</title></head>"
        b"<body><h1>405 Method Not Allowed</h1>"
        b"<p>Only GET and HEAD are supported.</p></body></html>"
    )

    headers = {
        "Content-Type": "text/html; charset=utf-8",
        "Allow": "GET, HEAD",
    }
    return build_http_response(405, headers, body)


def generate_400_response() -> bytes:
    body = (
        b"<html><head><title>400 Bad Request</title></head>"
        b"<body><h1>400 Bad Request</h1></body></html>"
    )

    headers = {
        "Content-Type": "text/html; charset=utf-8",
    }
    return build_http_response(400, headers, body)


def handle_client(client_socket, base_dir: str = "public") -> None:
    try:
        request_text = receive_http_request(client_socket)
        method, path, version = parse_request(request_text)

        if method not in {"GET", "HEAD"}:
            response = generate_405_response()
            client_socket.sendall(response)
            return

        target = get_file_path(path, base_dir=base_dir, allow_directory=False)
        if not target or not Path(target).is_file():
            response = generate_404_response()
            client_socket.sendall(response)
            return

        data = Path(target).read_bytes()
        mime = determine_content_type(target)

        headers = {
            "Content-Type": f"{mime}",
            "Content-Length": str(len(data)),
            "Connection": "close",
        }

        # 7) For HEAD: send headers only (no body)
        body = b"" if method == "HEAD" else data
        response = build_http_response(200, headers, body)
        client_socket.sendall(response)

    except ValueError as ve:
        body = (
            b"<html><head><title>400 Bad Request</title></head>"
            b"<body><h1>400 Bad Request</h1></body></html>"
        )
        headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Connection": "close",
        }
        response = build_http_response(400, headers, body)
        try:
            client_socket.sendall(response)
        except Exception:
            pass  # client may have already gone away

    except Exception as e:
        body = (
            b"<html><head><title>500 Internal Server Error</title></head>"
            b"<body><h1>500 Internal Server Error</h1></body></html>"
        )
        headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Connection": "close",
        }
        response = build_http_response(500, headers, body)
        try:
            client_socket.sendall(response)
        except Exception:
            pass

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
