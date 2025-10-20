import socket

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


def get_file_path(path: str) -> str:
    pass


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

    client_socket.close()
    server.close()


def main():
    start_server()


if __name__ == "__main__":
    main()
