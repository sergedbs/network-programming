"""Main HTTP server implementation."""

import socket
import signal
import logging
from pathlib import Path
from .config import HOST, PORT
from .network import SocketListener
from .http_protocol import RequestReceiver, RequestParser, ResponseBuilder
from .services import StaticFileService
from .handlers import ClientHandler


class SimpleHTTPServer:
    """Composed, extensible HTTP server."""

    def __init__(
        self,
        host: str = HOST,
        port: int = PORT,
        base_dir: str = "public",
        allow_directory_listing: bool = False,
    ):
        self.host = host
        self.port = port
        self.listener = SocketListener(host, port)
        self.logger = logging.getLogger(__name__)
        self._shutdown_requested = False

        receiver = RequestReceiver()
        parser = RequestParser()
        files = StaticFileService(
            base_dir=base_dir, allow_directory=allow_directory_listing
        )

        # Set up template directory (relative to this file)
        template_dir = Path(__file__).parent / "templates"
        responses = ResponseBuilder(template_dir=template_dir)

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
                    self.logger.info(
                        f"Connection from {client_addr[0]}:{client_addr[1]}"
                    )
                    self.handler.handle(client_socket, client_addr)
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
