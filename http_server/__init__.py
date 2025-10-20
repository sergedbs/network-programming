"""Simple HTTP Server - A lightweight static file server."""

__version__ = "1.0.0"

from .server import SimpleHTTPServer
from .config import HOST, PORT
from .templates import TemplateService

__all__ = ["SimpleHTTPServer", "HOST", "PORT", "TemplateService"]
