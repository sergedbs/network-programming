"""Request handlers - Client connection handling and request routing."""

import socket
import logging
from .http_protocol import RequestReceiver, RequestParser, ResponseBuilder
from .services import StaticFileService


class ClientHandler:
    """Coordinates receive -> parse -> route -> respond for one client socket."""

    def __init__(
        self,
        receiver: RequestReceiver,
        parser: RequestParser,
        files: StaticFileService,
        responses: ResponseBuilder,
        logger: logging.Logger | None = None,
    ):
        self.receiver = receiver
        self.parser = parser
        self.files = files
        self.responses = responses
        self.logger = logger or logging.getLogger(__name__)

    def handle(self, client_socket: socket.socket) -> None:
        try:
            request_text = self.receiver.receive(client_socket)
            req = self.parser.parse(request_text)

            self.logger.info(f"{req.method} {req.path} {req.version}")

            if req.method not in {"GET", "HEAD"}:
                self.logger.warning(f"405 Method Not Allowed: {req.method} {req.path}")
                client_socket.sendall(self.responses.error(405, "GET, HEAD"))
                return

            target = self.files.resolve(req.path)
            if not target or not target.is_file():
                self.logger.warning(f"404 Not Found: {req.path}")
                client_socket.sendall(self.responses.error(404))
                return

            data = self.files.read_bytes(target)
            content_type = self.files.content_type(target)

            headers = {
                "Content-Type": content_type,
                "Content-Length": str(len(data)),
                "Connection": "close",
            }
            body = b"" if req.method == "HEAD" else data
            client_socket.sendall(self.responses.build(200, headers, body))
            self.logger.info(f"200 OK: {req.path} ({len(data)} bytes)")

        except ValueError as e:
            self.logger.error(f"400 Bad Request: {e}")
            client_socket.sendall(self.responses.error(400))
        except Exception as e:
            self.logger.exception(f"500 Internal Server Error: {e}")
            client_socket.sendall(self.responses.error(500))
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
