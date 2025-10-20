"""Configuration constants for the HTTP server."""

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
