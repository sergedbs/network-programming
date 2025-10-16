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
    method, path, version = "GET", "/", "HTTP/1.1"

    if not request_text:
        return method, "/index.html", version

    lines = request_text.splitlines()
    if not lines:
        return method, "/index.html", version

    parts = lines[0].split()
    if len(parts) >= 1:
        method = parts[0]
    if len(parts) >= 2:
        raw_target = parts[1]
        qpos = raw_target.find("?")
        if qpos != -1:
            raw_target = raw_target[:qpos]
        path = raw_target or "/"
    if len(parts) >= 3:
        version = parts[2]

    if path == "/":
        path = "/index.html"

    return method, path, version


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
