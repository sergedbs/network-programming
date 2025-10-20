import socket
from pathlib import Path
import mimetypes
import logging
import signal
import sys
import argparse
from typing import NamedTuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

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
        # Set a timeout so accept() doesn't block indefinitely
        # This allows signal handlers to be processed
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


class RequestReceiver:
    """Reads request bytes until end-of-headers or size limit, then decodes."""

    def __init__(
        self, header_end: bytes = HEADER_END, max_header_bytes: int = MAX_HEADER_BYTES
    ):
        self.header_end = header_end
        self.max_header_bytes = max_header_bytes

    def receive(self, client_socket: socket.socket) -> str:
        data = bytearray()
        try:
            while self.header_end not in data:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > self.max_header_bytes:
                    raise ValueError("Request headers too large")
        except socket.timeout:
            raise ValueError("Request timed out")

        try:
            return data.decode("utf-8", errors="replace")
        except Exception:
            return ""


class RequestParser:
    """Parses the request line into an HTTPRequest."""

    VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}

    def parse(self, request_text: str) -> HTTPRequest:
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

        if method.upper() not in self.VALID_METHODS:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if not version.startswith("HTTP/"):
            raise ValueError(f"Invalid HTTP version: {version}")

        path = raw_path.split("?", 1)[0]
        if not path.startswith("/"):
            path = "/" + path
        if path == "/":
            path = "/index.html"

        return HTTPRequest(method.upper(), path, version)


class StaticFileService:
    """Resolves safe file paths and determines content types."""

    def __init__(self, base_dir: str = "public", allow_directory: bool = False):
        self.base_dir = Path(base_dir).resolve()
        self.allow_directory = allow_directory

    def resolve(self, request_path: str) -> Path | None:
        relative = request_path.lstrip("/")
        target = (self.base_dir / relative).resolve()
        try:
            target.relative_to(self.base_dir)
        except ValueError:
            return None  # path traversal attempt
        if not target.exists():
            return None
        if target.is_file():
            return target
        if self.allow_directory and target.is_dir():
            return target
        return None

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def content_type(self, path: Path) -> str:
        mimetype, _ = mimetypes.guess_type(str(path))
        return mimetype or "application/octet-stream"


class ResponseBuilder:
    """Builds HTTP responses and common error pages."""

    def __init__(
        self, server_name: str = SERVER_NAME, status_text: dict[int, str] = STATUS_TEXT
    ):
        self.server_name = server_name
        self.status_text = status_text

    def build(
        self, status_code: int, headers: dict, body: bytes | None = None
    ) -> bytes:
        reason = self.status_text.get(status_code, "OK")
        body = body or b""
        headers = dict(headers)  # copy to avoid mutating callers
        headers.setdefault("Content-Length", str(len(body)))
        headers.setdefault("Connection", "close")
        headers.setdefault("Server", self.server_name)

        lines = [f"HTTP/1.1 {status_code} {reason}"]
        for k, v in headers.items():
            lines.append(f"{k}: {v}")
        lines.append("")  # end of headers
        head = "\r\n".join(lines).encode("utf-8", errors="strict") + b"\r\n"
        return head + body

    @staticmethod
    def html_error_body(title: str, heading: str) -> bytes:
        return (
            f"<html><head><title>{title}</title></head>"
            f"<body><h1>{heading}</h1></body></html>"
        ).encode("utf-8")

    def html(
        self, status_code: int, body: bytes, extra_headers: dict | None = None
    ) -> bytes:
        headers = {"Content-Type": "text/html; charset=utf-8"}
        if extra_headers:
            headers.update(extra_headers)
        return self.build(status_code, headers, body)

    def error(self, status_code: int, allow_header: str | None = None) -> bytes:
        """Generate standard HTML error response for given status code."""
        reason = self.status_text.get(status_code, "Error")
        title = f"{status_code} {reason}"
        body = self.html_error_body(title, title)
        headers = {"Content-Type": "text/html; charset=utf-8"}
        if allow_header:
            headers["Allow"] = allow_header
        return self.build(status_code, headers, body)


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


class SimpleHTTPServer:
    """Composed, extensible HTTP server."""

    def __init__(self, host: str = HOST, port: int = PORT, base_dir: str = "public"):
        self.host = host
        self.port = port
        self.listener = SocketListener(host, port)
        self.logger = logging.getLogger(__name__)
        self._shutdown_requested = False

        receiver = RequestReceiver()
        parser = RequestParser()
        files = StaticFileService(base_dir=base_dir, allow_directory=False)
        responses = ResponseBuilder()
        self.handler = ClientHandler(receiver, parser, files, responses, self.logger)

    def shutdown(self) -> None:
        """Signal the server to stop accepting connections."""
        self._shutdown_requested = True
        self.logger.info("Shutdown signal received")

    def serve_forever(self) -> None:
        """Start the server and handle requests until shutdown is requested."""

        # Register signal handlers for graceful shutdown
        def signal_handler(signum: int, frame) -> None:
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.listener.start()
        self.logger.info(f"Server started on {self.host}:{self.port}")
        self.logger.info("Press Ctrl+C to stop the server")

        try:
            while not self._shutdown_requested:
                try:
                    client_socket, client_addr = self.listener.accept()
                    self.logger.debug(f"Connection from {client_addr}")
                    self.handler.handle(client_socket)
                except socket.timeout:
                    # Accept timed out, check shutdown flag and continue
                    continue
                except OSError:
                    # Socket was closed during shutdown
                    if self._shutdown_requested:
                        break
                    raise
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully (backup in case signal handler doesn't catch it)
            self.logger.info("Keyboard interrupt received")
            self._shutdown_requested = True
        except Exception as e:
            self.logger.exception(f"Fatal server error: {e}")
        finally:
            self.logger.info("Server shutting down gracefully")
            self.listener.close()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Simple HTTP Server - Serve static files over HTTP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Serve 'public' directory on 0.0.0.0:8080
  %(prog)s -d /var/www              # Serve /var/www directory
  %(prog)s -p 3000                  # Use port 3000
  %(prog)s -d ./dist -p 8000        # Serve ./dist on port 8000
  %(prog)s --host 127.0.0.1         # Listen only on localhost
        """,
    )

    parser.add_argument(
        "-d",
        "--dir",
        "--directory",
        dest="directory",
        default="public",
        help="Directory to serve (default: public)",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=PORT,
        help=f"Port to listen on (default: {PORT})",
    )

    parser.add_argument(
        "--host",
        default=HOST,
        help=f"Host/IP to bind to (default: {HOST})",
    )

    return parser.parse_args()


def main():
    """Main entry point for the HTTP server."""
    args = parse_arguments()

    # Validate and resolve the base directory
    # If it's a relative path, resolve it relative to the current working directory
    base_dir_path = Path(args.directory)
    if not base_dir_path.is_absolute():
        # For relative paths, use current working directory
        base_dir = Path.cwd() / base_dir_path
    else:
        base_dir = base_dir_path

    base_dir = base_dir.resolve()

    if not base_dir.exists():
        print(f"Error: Directory '{args.directory}' does not exist", file=sys.stderr)
        print(f"Looked for: {base_dir}", file=sys.stderr)
        sys.exit(1)

    if not base_dir.is_dir():
        print(f"Error: '{args.directory}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Check if directory is readable
    try:
        list(base_dir.iterdir())
    except PermissionError:
        print(
            f"Error: Permission denied to read directory '{args.directory}'",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Starting HTTP server...")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Directory: {base_dir}")
    print()

    try:
        server = SimpleHTTPServer(
            host=args.host, port=args.port, base_dir=str(base_dir)
        )
        server.serve_forever()
    except OSError as e:
        print(f"Error: Failed to start server - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
