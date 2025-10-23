"""Network layer - Socket listener for accepting client connections."""

import socket
from .config import BACKLOG, CLIENT_TIMEOUT_SECONDS


class SocketListener:
    """Owns the listening socket and accepts clients with a timeout set."""

    def __init__(
        self,
        host: str,
        port: int,
        backlog: int = BACKLOG,
        client_timeout: int = CLIENT_TIMEOUT_SECONDS,
    ):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.client_timeout = client_timeout
        self._server: socket.socket | None = None

    def start(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(self.backlog)
        server.settimeout(1.0)
        self._server = server

    def accept(self) -> tuple[socket.socket, tuple[str, int]]:
        if self._server is None:
            raise RuntimeError("Listener not started")
        client_socket, client_addr = self._server.accept()
        client_socket.settimeout(self.client_timeout)
        return client_socket, client_addr

    def close(self) -> None:
        try:
            if self._server:
                self._server.close()
        finally:
            self._server = None
