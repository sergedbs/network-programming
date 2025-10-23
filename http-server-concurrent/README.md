# Concurrent HTTP Server

A multithreaded HTTP/1.1 server implementation with request counting and rate limiting. Built from scratch using Python and raw TCP sockets, this educational project demonstrates concurrent programming, thread synchronization, and production-grade server features.

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Table of Contents

- [Features](#features)
- [Concurrency & Thread Safety](#concurrency--thread-safety)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [How It Works](#how-it-works)
- [Examples](#examples)
- [Development](#development)
- [License](#license)

## Features

### Core Features

- **Thread Pool Concurrency**: Handles multiple requests simultaneously using `ThreadPoolExecutor`
- **Request Counter**: Thread-safe tracking of requests per file path with atomic operations
- **Rate Limiting**: IP-based rate limiting (5 requests/second) using sliding window algorithm
- **Pure TCP Implementation**: Built on raw `socket` library without using high-level HTTP frameworks
- **HTTP/1.1 Compliant**: Proper request parsing and response formatting
- **Static File Serving**: Serves files with automatic MIME type detection
- **Directory Listings**: Beautiful HTML directory browser with request count statistics
- **Path Traversal Protection**: Secure path validation prevents directory escape attacks
- **Graceful Shutdown**: Proper signal handling (SIGINT, SIGTERM) with thread pool cleanup

### HTTP Protocol Support

- **Methods**: `GET`, `HEAD` (extensible for other methods)
- **Status Codes**: 200, 308, 400, 403, 404, 405, 429 (Too Many Requests), 500
- **Content Types**: Automatic MIME type detection for common file types
- **Headers**: Proper `Content-Type`, `Content-Length`, `Server`, and `Connection` headers
- **Rate Limiting**: HTTP 429 responses when client exceeds rate limit

### Developer Experience

- **Flexible CLI**: Rich command-line interface with multiple configuration options
- **Logging Levels**: Configurable logging (debug, info, warning, error, none)
- **Test Suite**: Performance, rate limiting, and thread-safety tests included
- **Docker Support**: Ready-to-use Dockerfile and docker-compose configuration
- **Clean Architecture**: Modular, testable design following SOLID principles

## Concurrency & Thread Safety

### Concurrency Model

This server uses a **thread pool** approach for handling concurrent requests:

- **Main Thread**: Accepts incoming connections in a loop
- **Worker Threads**: Handle requests from a pool (default: 10 workers)
- **ThreadPoolExecutor**: Python's built-in thread pool for efficient resource management

### Thread Safety Mechanisms

All shared state is protected with proper synchronization:

#### Request Counter (`counter.py`)

```python
with self._lock:
    self._counts[path] += 1  # Atomic increment
```

- Uses `threading.Lock` to prevent race conditions
- Thread-safe increment/get operations
- No data corruption under high concurrency

#### Rate Limiter (`rate_limiter.py`)

```python
with self._lock:
    # Sliding window algorithm
    # Remove expired timestamps
    # Check and update request count
```

- Sliding window algorithm with `deque` for O(1) operations
- Thread-safe timestamp management
- Per-IP request tracking

### Concurrency vs Parallelism

This implementation follows the **high-level (PLT) definition**:

- **Concurrency**: Program structured as independent request handlers
- **Parallelism**: Multiple threads executing simultaneously on multiple CPU cores
- **Both**: This server is concurrent in design AND parallel in execution (when GIL allows)

### Performance Benefits

- **Throughput**: Handles multiple requests simultaneously
- **Responsiveness**: No blocking on I/O operations
- **Scalability**: Configurable worker pool size
- **Efficiency**: Reuses threads instead of creating new ones per request

## Architecture

The server follows a **layered architecture** with thread-pool concurrency:

```txt
                    Main Thread (Accept Loop)
                            ↓
                    ThreadPoolExecutor
                    (Worker Pool: 10 threads)
                            ↓
┌─────────────────────────────────────────────────────┐
│         CLI Layer (cli.py)                          │
├─────────────────────────────────────────────────────┤
│      Server Layer (server.py)                       │
│      - Thread pool management                       │
│      - Connection dispatch                          │
├─────────────────────────────────────────────────────┤
│     Handler Layer (handlers.py)                     │
│     - Rate limiting (per IP)                        │
│     - Request counting (per path)                   │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ HTTP Layer   │  │ Services    │  │ Concurrent │ │
│  │ (protocol)   │  │ (services)  │  │ Components │ │
│  └──────────────┘  └─────────────┘  └────────────┘ │
│                                      - Counter      │
│                                      - RateLimiter  │
├─────────────────────────────────────────────────────┤
│    Network Layer (network.py)                       │
└─────────────────────────────────────────────────────┘
```

### Design Patterns

- **Thread Pool Pattern**: Efficient concurrent request handling with bounded resources
- **Composition over Inheritance**: Components are composed rather than inherited
- **Dependency Injection**: Dependencies passed explicitly for testability
- **Single Responsibility**: Each module has one clear purpose
- **Lock-Based Synchronization**: Thread-safe shared state management
- **Sliding Window Algorithm**: Efficient rate limiting with time-based cleanup

## Project Structure

```txt
concurrent-http-server/
├── server/                     # Server implementation
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # Entry point for `python -m server`
│   ├── cli.py                 # Command-line interface & argument parsing
│   ├── config.py              # Configuration constants & defaults
│   ├── server.py              # Main HTTP server with ThreadPoolExecutor
│   ├── network.py             # TCP socket listener & connection handling
│   ├── http_protocol.py       # HTTP request parsing & response building
│   ├── handlers.py            # Request routing with counter & rate limiter
│   ├── services.py            # File serving & directory listing logic
│   ├── templates.py           # HTML template loading & rendering
│   ├── counter.py             # Thread-safe request counter
│   ├── rate_limiter.py        # Thread-safe rate limiter (sliding window)
│   └── templates/             # HTML templates
│       ├── directory.html     # Directory listing with request counts
│       └── error.html         # Error page template
├── test/                       # Test suite
│   ├── performance_test.py    # Concurrent performance testing
│   ├── rate_limit_test.py     # Rate limiter verification
│   └── counter_test.py        # Thread-safety testing for counter
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
   cd network-programming/http-server-concurrent
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

**Configure thread pool size**:

```bash
MAX_WORKERS=20 python3 -m server
```

**Configure rate limiting**:

```bash
RATE_LIMIT_REQUESTS=10 RATE_LIMIT_WINDOW=1.0 python3 -m server
```

## Configuration

### Server Configuration

Configuration constants are defined in `server/config.py`:

```python
HOST = "0.0.0.0"                    # Bind address
PORT = 8080                         # Default port
ENABLE_DIR_LISTING = True           # Directory listing enabled
SUPPORTED_METHODS = {"GET", "HEAD"} # Supported HTTP methods

# Concurrency settings
MAX_WORKERS = 10                    # Thread pool size

# Rate limiting settings
RATE_LIMIT_REQUESTS = 5             # Max requests per window
RATE_LIMIT_WINDOW = 1.0             # Time window in seconds

# Network settings
BACKLOG = 100                       # Socket listen backlog
CLIENT_TIMEOUT_SECONDS = 5          # Client socket timeout
MAX_HEADER_BYTES = 64 * 1024        # Max request header size (64 KB)

# Server identification
SERVER_NAME = "SimplePythonSocketHTTP/1.0"
```

### Environment Variables

You can override configuration with environment variables:

- `SERVER_HOST`: Host to bind to (default: `0.0.0.0`)
- `SERVER_PORT`: Port to listen on (default: `8080`)
- `MAX_WORKERS`: Thread pool size (default: `10`)
- `RATE_LIMIT_REQUESTS`: Max requests per window (default: `5`)
- `RATE_LIMIT_WINDOW`: Time window in seconds (default: `1.0`)
- `CLIENT_TIMEOUT`: Socket timeout in seconds (default: `5`)
- `LOG_LEVEL`: Logging level (default: `info`)

### Logging Levels

- **`debug`**: All messages (connection details, request parsing, file access, thread info)
- **`info`**: General information (requests, responses, server lifecycle)
- **`warning`**: Warning messages (404s, 403s, 429s, invalid requests)
- **`error`**: Error messages (500s, exceptions)
- **`none`**: No logging output

## Testing

The server includes a comprehensive test suite to verify concurrency, thread-safety, and rate limiting.

### Prerequisites for testing

Install the `requests` library for testing:

```bash
pip install requests
```

### Performance Test

Tests concurrent request handling and measures throughput improvement over sequential processing:

```bash
python3 test/performance_test.py
```

**What it tests:**

- Sends 10 concurrent requests to the server
- Measures total time and average response time
- Compares concurrent vs sequential performance

**Expected result:** Total time should be close to single request time (~1s), not 10× that (sequential).

### Rate Limiting Test

Verifies the rate limiter correctly enforces request limits:

```bash
python3 test/rate_limit_test.py
```

**What it tests:**

- **Test 1 (Spam)**: Sends 20 rapid requests - expects rate limiting after 5 requests
- **Test 2 (Under Limit)**: Sends requests with delays - expects all to succeed

**Expected result:** First test should show HTTP 429 responses, second test should have all 200 OK.

### Counter Test

Validates thread-safe request counting without race conditions:

```bash
python3 test/counter_test.py
```

**What it tests:**

- Sends 50+ concurrent requests to same files
- Verifies counter increments correctly
- Checks directory listing shows accurate counts

**Expected result:** Request counts in directory listing should match the number of requests made.

### Verification

After running tests, open the directory listing in your browser:

```bash
open http://localhost:8080/
```

Check that the "Requests" column shows accurate counts for each file.

## Docker Deployment

### Using Docker

**Build the image**:

```bash
docker build -t http-server-concurrent .
```

**Run the container**:

```bash
docker run -p 8080:8080 -v $(pwd)/public:/app/public:ro http-server-concurrent
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

### Concurrent Request Flow

1. **TCP Connection**: Main thread accepts client connection
2. **Thread Dispatch**: Connection submitted to ThreadPoolExecutor
3. **Worker Thread Picks Up**: Available worker thread handles the request
4. **Rate Limit Check**: Verify client IP hasn't exceeded rate limit (5 req/sec)
   - If exceeded: Send HTTP 429, close connection
   - If allowed: Continue processing
5. **Request Reception**: Read raw bytes until `\r\n\r\n` (end of headers)
6. **Request Parsing**: HTTP request line parsed into method, path, version
7. **Request Counter**: Increment counter for this path (thread-safe)
8. **Path Normalization**: URL decoded, query params stripped, relative path resolved
9. **Path Validation**: Security check prevents directory traversal attacks
10. **Resource Resolution**: Requested path mapped to filesystem
11. **Response Generation**:
    - **File**: Read file, detect MIME type, send with 200 OK
    - **Directory**: Generate HTML listing with request counts, send with 200 OK
    - **Not Found**: Send 404 error page
    - **Forbidden**: Send 403 error page
    - **Error**: Send 500 error page
12. **Connection Close**: Socket closed, worker thread returns to pool

### Key Components

#### 0. Concurrency Layer

```python
class ThreadPoolExecutor:
    """Python's built-in thread pool"""
    - Manages worker threads
    - Queues incoming requests
    - Reuses threads efficiently

class RequestCounter:
    """Thread-safe request counter"""
    - Tracks requests per file path
    - Uses threading.Lock for synchronization
    - Prevents race conditions

class RateLimiter:
    """Thread-safe rate limiter"""
    - Sliding window algorithm
    - Per-IP request tracking
    - Automatic cleanup of old timestamps
    - Uses threading.Lock for synchronization
```

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
    """Coordinates request handling with concurrency features"""
    - Checks rate limiter (per client IP)
    - Receives and parses request
    - Increments request counter (thread-safe)
    - Routes to appropriate handler
    - Generates response with request counts
    - Handles errors gracefully
```

#### 5. Server Layer (`server.py`)

```python
class SimpleHTTPServer:
    """Main server with thread pool"""
    - Creates ThreadPoolExecutor with N workers
    - Starts socket listener
    - Accepts connections in main thread
    - Submits each connection to thread pool
    - Handles shutdown signals
    - Gracefully shuts down thread pool
    - Logs activity
```

### Security Features

1. **Path Traversal Prevention**: All paths validated with `path.relative_to(base_dir)`
2. **Rate Limiting**: Prevents DoS attacks by limiting requests per IP
3. **Request Size Limits**: Maximum 64 KB header size prevents memory exhaustion
4. **Socket Timeouts**: 5-second timeout prevents hanging connections
5. **Input Validation**: HTTP method and version validated before processing
6. **Thread Pool Bounds**: Limited worker threads prevent resource exhaustion
7. **Thread-Safe State**: All shared state protected with locks
8. **Error Handling**: All exceptions caught and logged, never exposed to client

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
2025-10-21 10:31:15 [INFO] Thread pool size: 10 workers
2025-10-21 10:31:20 [INFO] Connection from 127.0.0.1:54321
2025-10-21 10:31:20 [INFO] 127.0.0.1:54321 - GET /index.html HTTP/1.1
2025-10-21 10:31:20 [DEBUG] Request count for /index.html: 1
2025-10-21 10:31:20 [INFO] 127.0.0.1:54321 - 200 OK: /index.html (1234 bytes)
```

### Example 3: Directory Browsing with Request Counts

Visit `http://localhost:8080/` with directory listing enabled to see:

- Parent directory link (`..`)
- List of files and subdirectories
- File sizes (human-readable: KB, MB, GB)
- Last modified timestamps
- **Request counts** for each file (new!)
- Clickable links to navigate

### Example 4: Rate Limiting in Action

**Test rate limiting**:

```bash
# Send multiple requests rapidly
for i in {1..10}; do curl http://localhost:8080/ & done
```

**Expected behavior**:

- First 5 requests: HTTP 200 OK
- Remaining requests: HTTP 429 Too Many Requests

**429 Response**:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: text/html; charset=utf-8
Content-Length: 234
Connection: close
Server: SimplePythonSocketHTTP/1.0

<html>
  <head><title>429 Too Many Requests</title></head>
  <body>
    <h1>429 Too Many Requests</h1>
    <p>Rate limit exceeded. Please try again later.</p>
  </body>
</html>
```

### Example 5: Handling Errors

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
- **`server.py`**: Main server loop, thread pool management, signal handling
- **`network.py`**: Low-level TCP socket operations
- **`http_protocol.py`**: HTTP parsing and response building
- **`handlers.py`**: Request routing, rate limiting, request counting
- **`services.py`**: File system operations and business logic
- **`templates.py`**: HTML template rendering
- **`counter.py`**: Thread-safe request counter
- **`rate_limiter.py`**: Thread-safe rate limiter with sliding window
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

### HTTP Protocol

- [RFC 9110 - HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [RFC 9112 - HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)
- [MIME Types Reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types)

### Python Programming

- [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)
- [Python Threading Documentation](https://docs.python.org/3/library/threading.html)
- [ThreadPoolExecutor Documentation](https://docs.python.org/3/library/concurrent.futures.html)

### Concurrency Concepts

- [MIT 6.102 - Concurrency](https://web.mit.edu/6.102/www/sp25/classes/14-concurrency/)
- [The Art of Multiprocessor Programming](https://www.elsevier.com/books/the-art-of-multiprocessor-programming/herlihy/978-0-12-415950-1)

---

Made with ❤️ using Python and TCP sockets
