"""Request handlers - Client connection handling and request routing."""

import socket
import logging
from .http_protocol import RequestReceiver, RequestParser, ResponseBuilder
from .services import StaticFileService
from .config import SUPPORTED_METHODS
from .counter import RequestCounter
from .rate_limiter import RateLimiter


class ClientHandler:
    """Coordinates receive -> parse -> route -> respond for one client socket."""

    def __init__(
        self,
        receiver: RequestReceiver,
        parser: RequestParser,
        files: StaticFileService,
        responses: ResponseBuilder,
        logger: logging.Logger | None = None,
        counter: RequestCounter | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        self.receiver = receiver
        self.parser = parser
        self.files = files
        self.responses = responses
        self.logger = logger or logging.getLogger(__name__)
        self.counter = counter
        self.rate_limiter = rate_limiter

    def handle(self, client_socket: socket.socket, client_addr: tuple = None) -> None:
        req = None
        addr_str = f"{client_addr[0]}:{client_addr[1]}" if client_addr else "unknown"
        client_ip = client_addr[0] if client_addr else "unknown"

        try:
            # Check rate limit first
            if self.rate_limiter and not self.rate_limiter.is_allowed(client_ip):
                self.logger.warning(
                    f"{addr_str} - 429 Too Many Requests: Rate limit exceeded"
                )
                client_socket.sendall(self.responses.error(429))
                return

            request_text = self.receiver.receive(client_socket)
            req = self.parser.parse(request_text)

            self.logger.info(f"{addr_str} - {req.method} {req.path} {req.version}")

            # Increment counter for this path
            if self.counter:
                count = self.counter.increment(req.path)
                self.logger.debug(f"Request count for {req.path}: {count}")

            if req.method not in SUPPORTED_METHODS:
                self.logger.warning(
                    f"{addr_str} - 405 Method Not Allowed: {req.method} {req.path} "
                    f"(supported: {', '.join(sorted(SUPPORTED_METHODS))})"
                )
                client_socket.sendall(
                    self.responses.error(405, ", ".join(sorted(SUPPORTED_METHODS)))
                )
                return

            target = self.files.resolve(req.path)
            if not target:
                self.logger.warning(f"{addr_str} - 404 Not Found: {req.path}")
                client_socket.sendall(self.responses.error(404))
                return

            if target.is_dir():
                if not req.path.endswith("/") and req.path != "/":
                    redirect_path = req.path + "/"
                    headers = {
                        "Location": redirect_path,
                        "Content-Length": "0",
                        "Connection": "close",
                    }
                    client_socket.sendall(self.responses.build(308, headers, b""))
                    self.logger.info(
                        f"{addr_str} - 308 Permanent Redirect: {req.path} -> {redirect_path}"
                    )
                    return

                index_file = self.files.find_index(target)
                if index_file:
                    data = self.files.read_bytes(index_file)
                    content_type = self.files.content_type(index_file)
                    headers = {
                        "Content-Type": content_type,
                        "Content-Length": str(len(data)),
                        "Connection": "close",
                    }
                    body = b"" if req.method == "HEAD" else data
                    client_socket.sendall(self.responses.build(200, headers, body))
                    self.logger.info(
                        f"{addr_str} - 200 OK: {req.path} (index: {index_file.name}, {len(data)} bytes)"
                    )
                    return

                if not self.files.allow_directory:
                    self.logger.warning(
                        f"{addr_str} - 403 Forbidden: Directory listing disabled for {req.path}"
                    )
                    client_socket.sendall(
                        self.responses.error(403, "Directory listing is disabled")
                    )
                    return

                entries = self.files.list_directory(target)
                # Add request counts to directory entries if counter is available
                if self.counter:
                    for entry in entries:
                        entry_path = entry["path"]
                        entry["request_count"] = self.counter.get(entry_path)

                response = self.responses.directory_listing(req.path, entries)
                client_socket.sendall(response)
                self.logger.info(
                    f"{addr_str} - 200 OK: {req.path} (directory listing, {len(entries)} entries)"
                )
                return

            if target.is_file():
                data = self.files.read_bytes(target)
                content_type = self.files.content_type(target)

                headers = {
                    "Content-Type": content_type,
                    "Content-Length": str(len(data)),
                    "Connection": "close",
                }
                body = b"" if req.method == "HEAD" else data
                client_socket.sendall(self.responses.build(200, headers, body))
                self.logger.info(f"{addr_str} - 200 OK: {req.path} ({len(data)} bytes)")
                return

            self.logger.warning(
                f"{addr_str} - 404 Not Found: {req.path} (not a file or directory)"
            )
            client_socket.sendall(self.responses.error(404))
            return

        except ValueError as e:
            request_info = f"{req.method} {req.path}" if req else "(parse failed)"
            self.logger.error(f"{addr_str} - 400 Bad Request: {request_info} - {e}")
            client_socket.sendall(self.responses.error(400))
        except Exception as e:
            request_info = f"{req.method} {req.path}" if req else "(unknown)"
            self.logger.exception(
                f"{addr_str} - 500 Internal Server Error: {request_info} - {e}"
            )
            client_socket.sendall(self.responses.error(500))
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
