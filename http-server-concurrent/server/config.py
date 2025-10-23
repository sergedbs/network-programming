"""Configuration constants for the HTTP server."""

import os
import logging

HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", 8080))

ENABLE_DIR_LISTING = os.getenv("ENABLE_DIR_LISTING", "true").lower() in (
    "true",
    "1",
    "yes",
    "enabled",
)

INDEX_FILES = ["index.html", "index.htm"]

SUPPORTED_METHODS = {"GET", "HEAD"}

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "none": logging.CRITICAL + 1,
}
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()

STATUS_TEXT = {
    200: "OK",
    308: "Permanent Redirect",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    429: "Too Many Requests",
    500: "Internal Server Error",
}

BACKLOG = 100
CLIENT_TIMEOUT_SECONDS = int(os.getenv("CLIENT_TIMEOUT", "5"))
HEADER_END = b"\r\n\r\n"
MAX_HEADER_BYTES = 64 * 1024
SERVER_NAME = "SimplePythonSocketHTTP/1.0"

# Concurrency settings
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))

# Rate limiting settings
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
RATE_LIMIT_WINDOW = float(os.getenv("RATE_LIMIT_WINDOW", "1.0"))
