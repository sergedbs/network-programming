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


def start_server():
    server = create_socket(HOST, PORT)
    print(f"Starting server on {HOST}:{PORT}")
    input("")
    server.close()


def main():
    start_server()


if __name__ == "__main__":
    main()
