"""Main HTTP server implementation."""

import socket
import signal
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from .config import HOST, PORT, MAX_WORKERS
from .network import SocketListener
from .http_protocol import RequestReceiver, RequestParser, ResponseBuilder
from .services import StaticFileService
from .handlers import ClientHandler
from .counter import RequestCounter
from .rate_limiter import RateLimiter


class SimpleHTTPServer:
    """Composed, extensible HTTP server with thread pool for concurrent request handling."""

    def __init__(
        self,
        host: str = HOST,
        port: int = PORT,
        base_dir: str = "public",
        allow_directory_listing: bool = False,
        max_workers: int = MAX_WORKERS,
    ):
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.listener = SocketListener(host, port)
        self.logger = logging.getLogger(__name__)
        self._shutdown_requested = False
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        receiver = RequestReceiver()
        parser = RequestParser()
        files = StaticFileService(
            base_dir=base_dir, allow_directory=allow_directory_listing
        )

        template_dir = Path(__file__).parent / "templates"
        responses = ResponseBuilder(template_dir=template_dir)

        # Create thread-safe counter and rate limiter
        counter = RequestCounter()
        rate_limiter = RateLimiter()

        self.handler = ClientHandler(
            receiver, parser, files, responses, self.logger, counter, rate_limiter
        )

    def shutdown(self) -> None:
        """Signal the server to stop accepting connections."""
        self._shutdown_requested = True
        self.logger.info("Shutdown signal received")
        self.executor.shutdown(wait=True, cancel_futures=False)

    def serve_forever(self) -> None:
        """Start the server and handle requests until shutdown is requested."""

        def signal_handler(signum: int, frame) -> None:
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.listener.start()
        self.logger.info(f"Server started on {self.host}:{self.port}")
        self.logger.info(f"Thread pool size: {self.max_workers} workers")
        self.logger.info("Press Ctrl+C to stop the server")

        try:
            while not self._shutdown_requested:
                try:
                    client_socket, client_addr = self.listener.accept()
                    self.logger.info(
                        f"Connection from {client_addr[0]}:{client_addr[1]}"
                    )
                    # Submit to thread pool instead of handling directly
                    self.executor.submit(
                        self._handle_client, client_socket, client_addr
                    )
                except socket.timeout:
                    continue
                except OSError:
                    if self._shutdown_requested:
                        break
                    raise
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self._shutdown_requested = True
        except Exception as e:
            self.logger.exception(f"Fatal server error: {e}")
        finally:
            self.logger.info("Server shutting down gracefully")
            self.executor.shutdown(wait=True)
            self.listener.close()

    def _handle_client(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """Handle a client connection in a thread."""
        try:
            self.handler.handle(client_socket, client_addr)
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
