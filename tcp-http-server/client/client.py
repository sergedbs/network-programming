"""HTTP Client - Main client orchestration."""

from .cli import ClientArgs
from .handlers import ResponseHandler
from .http_protocol import HTTPClient


def run_client(args: ClientArgs) -> None:
    """
    Run HTTP client with parsed arguments.

    Args:
        args: Parsed command-line arguments
    """
    # Create HTTP client
    client = HTTPClient(args.host, args.port, args.timeout)

    # Create response handler
    handler = ResponseHandler(args.directory)

    try:
        # Make request
        print(f"Requesting: http://{args.host}:{args.port}{args.path}")
        response = client.get(args.path)

        # Handle response
        handler.handle(response, args.path)

    except ConnectionError as e:
        print(f"Connection error: {e}")
    except ValueError as e:
        print(f"Invalid response: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
