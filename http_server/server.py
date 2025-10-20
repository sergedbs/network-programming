import socket
from pathlib import Path
import mimetypes

HOST = "0.0.0.0"
PORT = 8080


def create_socket(host: str, port: int) -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    server.setblocking(True)
    return server


def accept_connection(server: socket.socket) -> socket.socket:
    client_socket, client_address = server.accept()
    client_socket.settimeout(5)
    return client_socket, client_address


def receive_http_request(client_socket: socket.socket) -> str:
    HEADER_END = b"\r\n\r\n"
    data = bytearray()

    while HEADER_END not in data:
        chunk = client_socket.recv(4096)
        if not chunk:
            break
        data.extend(chunk)

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


def start_server():
    print(f"Starting server on {HOST}:{PORT}")
    server = create_socket(HOST, PORT)

    print("Waiting for a client connection...")
    client_socket, client_address = accept_connection(server)
    print(f"Connection established with {client_address}")

    request = receive_http_request(client_socket)
    print("Received HTTP request:")
    print(request)

    method, path, version = parse_request(request)
    print(f"Parsed Request - Method: {method}, Path: {path}, Version: {version}")

    file_path = get_file_path(path)
    print(f"Resolved file path: {file_path}")
    if file_path:
        content_type = determine_content_type(file_path)
        response_body = file_path.read_bytes()
        response_headers = (
            f"{version} 200 OK\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            f"\r\n"
        )
    else:
        response_body = b"404 Not Found"
        response_headers = (
            f"{version} 404 Not Found\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            f"\r\n"
        )

    response = response_headers.encode("utf-8") + response_body
    client_socket.sendall(response)
    print("Response sent to client.")

    client_socket.close()
    server.close()


def main():
    start_server()


if __name__ == "__main__":
    main()
