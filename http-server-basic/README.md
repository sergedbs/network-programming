# TCP HTTP Server

A production-ready HTTP/1.1 server implementation built from scratch using Python and raw TCP sockets. This educational project demonstrates low-level network programming, HTTP protocol implementation, and clean software architecture principles.

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [How It Works](#how-it-works)
- [Examples](#examples)
- [Development](#development)
- [License](#license)

## Features

### Core Features

- **Pure TCP Implementation**: Built on raw `socket` library without using high-level HTTP frameworks
- **HTTP/1.1 Compliant**: Proper request parsing and response formatting
- **Static File Serving**: Serves files with automatic MIME type detection
- **Directory Listings**: Beautiful, responsive HTML directory browser (optional)
- **Path Traversal Protection**: Secure path validation prevents directory escape attacks
- **Graceful Shutdown**: Proper signal handling (SIGINT, SIGTERM) for clean server termination

### HTTP Protocol Support

- **Methods**: `GET`, `HEAD` (extensible for other methods)
- **Status Codes**: 200, 400, 403, 404, 405, 500
- **Content Types**: Automatic MIME type detection for common file types
- **Headers**: Proper `Content-Type`, `Content-Length`, `Server`, and `Connection` headers

### Developer Experience

- **Flexible CLI**: Rich command-line interface with multiple configuration options
- **Logging Levels**: Configurable logging (debug, info, warning, error, none)
- **Docker Support**: Ready-to-use Dockerfile and docker-compose configuration
- **Clean Architecture**: Modular, testable design following SOLID principles

## Architecture

The server follows a **layered architecture** with clear separation of concerns:

```txt
┌─────────────────────────────────────────┐
│         CLI Layer (cli.py)              │  - Argument parsing & validation
├─────────────────────────────────────────┤
│      Server Layer (server.py)           │  - Main server loop & lifecycle
├─────────────────────────────────────────┤
│     Handler Layer (handlers.py)         │  - Request routing & error handling
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────┐  │
│  │ HTTP Layer  │  │ Services Layer   │  │
│  │ (protocol)  │  │ (services)       │  │  - HTTP parsing & File operations
│  └─────────────┘  └──────────────────┘  │ 
├─────────────────────────────────────────┤
│    Network Layer (network.py)           │  - TCP socket management
└─────────────────────────────────────────┘
```

### Design Patterns

- **Composition over Inheritance**: Components are composed rather than inherited
- **Dependency Injection**: Dependencies passed explicitly for testability
- **Single Responsibility**: Each module has one clear purpose
- **Template Method**: Template service for flexible HTML rendering

## Project Structure

```txt
http-server-basic/
├── server/                     # Server implementation
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # Entry point for `python -m server`
│   ├── cli.py                 # Command-line interface & argument parsing
│   ├── config.py              # Configuration constants & defaults
│   ├── server.py              # Main HTTP server class & event loop
│   ├── network.py             # TCP socket listener & connection handling
│   ├── http_protocol.py       # HTTP request parsing & response building
│   ├── handlers.py            # Request routing & client connection handling
│   ├── services.py            # File serving & directory listing logic
│   ├── templates.py           # HTML template loading & rendering
│   └── templates/             # HTML templates
│       ├── directory.html     # Directory listing template
│       └── error.html         # Error page template
├── public/                     # Default directory to serve
│   ├── index.html             # Sample HTML page
│   ├── style.css              # Sample CSS file
│   ├── image.png              # Sample image
│   ├── Cat.pdf                # Sample PDF document
│   ├── favicon.ico            # Favicon
│   └── subdir/                # Sample subdirectory
│       ├── Cat.pdf            # Nested file
│       └── images/            # Nested images directory
│           └── image.png
├── downloads/                  # Directory for downloaded files
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── LICENSE                     # License file
└── README.md                   # This file
```

## Installation

### Prerequisites

- **Python 3.13+** (or any Python 3.8+)
- **Docker** (optional, for containerized deployment)

### Local Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/sergedbs/network-programming.git
   cd network-programming/http-server-basic
   ```

2. **No dependencies required!** This project uses only Python standard library.

3. **Verify installation**:

   ```bash
   python3 -m server --help
   ```

## Usage

### Basic Usage

**Start the server with default settings** (serves `public/` on `0.0.0.0:8080`):

```bash
python3 -m server
```

**Access the server**:

- Open your browser to `http://localhost:8080`
- Or use curl: `curl http://localhost:8080`

### Command-Line Options

```bash
python3 -m server [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-d, --dir, --directory` | Directory to serve | `public` |
| `-p, --port` | Port to listen on (1-65535) | `8080` |
| `--host` | Host/IP to bind to | `0.0.0.0` |
| `--dir-listing` | Enable/disable directory listing (`enabled`/`disabled`) | `enabled` |
| `--log-level` | Logging level (`debug`/`info`/`warning`/`error`/`none`) | `info` |
| `-h, --help` | Show help message | - |

### Common Usage Examples

**Serve a specific directory on a custom port**:

```bash
python3 -m server -d /var/www -p 3000
```

**Serve only on localhost (127.0.0.1)**:

```bash
python3 -m server --host 127.0.0.1
```

**Disable directory listing for security**:

```bash
python3 -m server --dir-listing disabled
```

**Enable debug logging**:

```bash
python3 -m server --log-level debug
```

**Serve current directory**:

```bash
python3 -m server -d .
```

## Configuration

### Server Configuration

Configuration constants are defined in `server/config.py`:

```python
HOST = "0.0.0.0"                    # Bind address
PORT = 8080                         # Default port
ENABLE_DIR_LISTING = True           # Directory listing enabled
SUPPORTED_METHODS = {"GET", "HEAD"} # Supported HTTP methods

# Network settings
BACKLOG = 100                       # Socket listen backlog
CLIENT_TIMEOUT_SECONDS = 5          # Client socket timeout
MAX_HEADER_BYTES = 64 * 1024        # Max request header size (64 KB)

# Server identification
SERVER_NAME = "SimplePythonSocketHTTP/1.0"
```

### Logging Levels

- **`debug`**: All messages (connection details, request parsing, file access)
- **`info`**: General information (requests, responses, server lifecycle)
- **`warning`**: Warning messages (404s, 403s, invalid requests)
- **`error`**: Error messages (500s, exceptions)
- **`none`**: No logging output

## Docker Deployment

### Using Docker

**Build the image**:

```bash
docker build -t http-server-basic .
```

**Run the container**:

```bash
docker run -p 8080:8080 -v $(pwd)/public:/app/public:ro http-server-basic
```

### Using Docker Compose

**Start the server**:

```bash
docker-compose up
```

**Start in detached mode**:

```bash
docker-compose up -d
```

**Stop the server**:

```bash
docker-compose down
```

**View logs**:

```bash
docker-compose logs -f
```

### Docker Configuration

The `docker-compose.yml` includes:

- **Port mapping**: `8080:8080`
- **Volume mounts**: `public/` mounted as read-only, `downloads/` as writable
- **Restart policy**: Restarts on failure (max 3 attempts)
- **Graceful shutdown**: 2-second grace period with SIGTERM signal

## How It Works

### Request Flow

1. **TCP Connection**: Client connects to server socket
2. **Request Reception**: Server reads raw bytes until `\r\n\r\n` (end of headers)
3. **Request Parsing**: HTTP request line parsed into method, path, version
4. **Path Normalization**: URL decoded, query params stripped, relative path resolved
5. **Path Validation**: Security check prevents directory traversal attacks
6. **Resource Resolution**: Requested path mapped to filesystem
7. **Response Generation**:
   - **File**: Read file, detect MIME type, send with 200 OK
   - **Directory**: Generate HTML listing (if enabled), send with 200 OK
   - **Not Found**: Send 404 error page
   - **Forbidden**: Send 403 error page
   - **Error**: Send 500 error page
8. **Connection Close**: Socket closed after response sent

### Key Components

#### 1. Network Layer (`network.py`)

```python
class SocketListener:
    """Manages TCP socket lifecycle"""
    - Creates and binds socket
    - Listens for connections
    - Sets timeouts on client sockets
    - Handles socket cleanup
```

#### 2. HTTP Protocol Layer (`http_protocol.py`)

```python
class RequestReceiver:
    """Reads HTTP request from socket"""
    - Reads bytes until \r\n\r\n
    - Enforces max header size limit
    - Handles socket timeouts

class RequestParser:
    """Parses HTTP request line"""
    - Validates HTTP method
    - Validates HTTP version
    - Normalizes request path
    - Strips query parameters

class ResponseBuilder:
    """Builds HTTP responses"""
    - Formats status line
    - Generates headers
    - Renders HTML templates
    - Creates error pages
```

#### 3. Services Layer (`services.py`)

```python
class StaticFileService:
    """Handles file operations"""
    - Resolves request paths securely
    - Prevents path traversal (../)
    - Detects MIME types
    - Lists directory contents
    - Formats file sizes
```

#### 4. Handler Layer (`handlers.py`)

```python
class ClientHandler:
    """Coordinates request handling"""
    - Receives request
    - Parses request
    - Routes to appropriate handler
    - Generates response
    - Handles errors gracefully
```

#### 5. Server Layer (`server.py`)

```python
class SimpleHTTPServer:
    """Main server loop"""
    - Starts socket listener
    - Accepts connections
    - Spawns handlers (synchronous)
    - Handles shutdown signals
    - Logs activity
```

### Security Features

1. **Path Traversal Prevention**: All paths validated with `path.relative_to(base_dir)`
2. **Request Size Limits**: Maximum 64 KB header size prevents memory exhaustion
3. **Socket Timeouts**: 5-second timeout prevents hanging connections
4. **Input Validation**: HTTP method and version validated before processing
5. **Error Handling**: All exceptions caught and logged, never exposed to client

## Examples

### Example 1: Serving Static Website

```bash
# Serve a static website from ./dist directory
python3 -m server -d ./dist -p 8000 --dir-listing disabled
```

**Output**:

```log
Starting HTTP server...
  Host: 0.0.0.0
  Port: 8000
  Directory: /path/to/dist
  Directory Listing: Disabled
  Log Level: info

2025-10-21 10:30:00 [INFO] Server started on 0.0.0.0:8000
2025-10-21 10:30:00 [INFO] Press Ctrl+C to stop the server
```

### Example 2: Development with Debug Logging

```bash
# Serve with debug logging to see all details
python3 -m server --log-level debug
```

**Sample log output**:

```log
2025-10-21 10:31:15 [INFO] Server started on 0.0.0.0:8080
2025-10-21 10:31:20 [INFO] Connection from 127.0.0.1:54321
2025-10-21 10:31:20 [INFO] 127.0.0.1:54321 - GET /index.html HTTP/1.1
2025-10-21 10:31:20 [INFO] 127.0.0.1:54321 - 200 OK: /index.html (1234 bytes)
```

### Example 3: Directory Browsing

Visit `http://localhost:8080/subdir/` with directory listing enabled to see:

- Parent directory link (`..`)
- List of files and subdirectories
- File sizes (human-readable: KB, MB, GB)
- Last modified timestamps
- Clickable links to navigate

### Example 4: Handling Errors

**404 Not Found**:

```bash
curl http://localhost:8080/nonexistent.html
```

Response:

```html
HTTP/1.1 404 Not Found
Content-Type: text/html; charset=utf-8
Content-Length: 123
Connection: close
Server: SimplePythonSocketHTTP/1.0

<html>
  <head><title>404 Not Found</title></head>
  <body>
    <h1>404 Not Found</h1>
    <p>The requested resource was not found on this server.</p>
  </body>
</html>
```

**403 Forbidden** (when directory listing is disabled):

```bash
python3 -m server --dir-listing disabled
curl http://localhost:8080/subdir/
```

### Example 5: Testing with curl

```bash
# GET request
curl -v http://localhost:8080/index.html

# HEAD request (no body)
curl -I http://localhost:8080/index.html

# Download a file
curl -O http://localhost:8080/Cat.pdf

# Test with custom headers
curl -H "User-Agent: MyClient/1.0" http://localhost:8080/
```

## Development

### Code Organization

The project follows a **modular architecture** with clear responsibilities:

- **`cli.py`**: Entry point, argument parsing, validation
- **`server.py`**: Main server loop, signal handling, composition
- **`network.py`**: Low-level TCP socket operations
- **`http_protocol.py`**: HTTP parsing and response building
- **`handlers.py`**: Request routing and error handling
- **`services.py`**: File system operations and business logic
- **`templates.py`**: HTML template rendering
- **`config.py`**: Configuration constants

### Extending the Server

#### Adding New HTTP Methods

1. Add method to `SUPPORTED_METHODS` in `config.py`:

   ```python
   SUPPORTED_METHODS = {"GET", "HEAD", "POST"}
   ```

2. Handle in `handlers.py`:

   ```python
   if req.method == "POST":
       # Handle POST request
       pass
   ```

#### Adding Custom Error Pages

1. Create template in `server/templates/`:

   ```html
   <!-- custom_error.html -->
   <html>
     <head><title>{status_code} {status_text}</title></head>
     <body>
       <h1>{status_code} {status_text}</h1>
       <p>{message}</p>
     </body>
   </html>
   ```

2. Use in `ResponseBuilder`:

   ```python
   html = self.template_service.load_template("custom_error")
   ```

#### Adding Middleware

Extend `ClientHandler` to add middleware:

```python
class ClientHandler:
    def handle(self, client_socket, client_addr):
        # Pre-processing middleware
        self._log_request(client_addr)
        self._check_rate_limit(client_addr)
        
        # Normal handling
        # ...
        
        # Post-processing middleware
        self._update_metrics()
```

### Testing

**Manual Testing**:

```bash
# Terminal 1: Start server
python3 -m server --log-level debug

# Terminal 2: Test with curl
curl -v http://localhost:8080/
curl -I http://localhost:8080/index.html
curl http://localhost:8080/nonexistent
```

**Load Testing** (using ApacheBench):

```bash
ab -n 1000 -c 10 http://localhost:8080/index.html
```

### Performance Considerations

- **Synchronous I/O**: Current implementation handles one request at a time
- **No Caching**: Files read from disk on every request
- **Production Use**: Consider adding:
  - Threading or async I/O for concurrent connections
  - Response caching (ETag, Last-Modified headers)
  - Connection keep-alive
  - Request body parsing for POST/PUT
  - Compression (gzip, deflate)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

- [RFC 9110 - HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [RFC 9112 - HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)
- [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)
- [MIME Types Reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types)

---

Made with ❤️ using Python and TCP sockets
