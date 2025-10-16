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
    request = client_socket.recv(1024).decode("utf-8")
    return request


def start_server():
    print(f"Starting server on {HOST}:{PORT}")
    server = create_socket(HOST, PORT)

    print("Waiting for a client connection...")
    client_socket, client_address = accept_connection(server)
    print(f"Connection established with {client_address}")

    request = receive_http_request(client_socket)
    print("Received HTTP request:")
    print(request)

    client_socket.close()
    server.close()


def main():
    start_server()


if __name__ == "__main__":
    main()
