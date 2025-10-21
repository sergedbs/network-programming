"""Configuration constants for the HTTP server."""

import logging

HOST = "0.0.0.0"
PORT = 8080

SUPPORTED_METHODS = {"GET", "HEAD"}

# Logging configuration
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "none": logging.CRITICAL + 1,  # Disable all logging
}
DEFAULT_LOG_LEVEL = "info"

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
