# Network Programming Projects

A collection of educational projects demonstrating network programming concepts, concurrency, and HTTP protocol implementation using Python and raw TCP sockets.

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Projects

### 1. HTTP Server - Basic (`http-server-basic/`)

A foundational HTTP/1.1 server implementation built from scratch using raw TCP sockets.

**Key Features:**

- Pure TCP implementation without high-level frameworks
- HTTP/1.1 compliant request parsing and response formatting
- Static file serving with automatic MIME type detection
- Beautiful directory listings with responsive HTML templates
- Path traversal protection for security
- Graceful shutdown handling

**Learning Focus:**

- Low-level socket programming
- HTTP protocol fundamentals
- Request/response lifecycle
- File system operations
- Security best practices

[Read more](http-server-basic/README.md)

### 2. HTTP Server - Concurrent (`http-server-concurrent/`)

An enhanced multithreaded HTTP/1.1 server with request counting, rate limiting, and thread-safe concurrent request handling.

**Key Features:**

- **Thread Pool Concurrency**: Handles multiple requests simultaneously using `ThreadPoolExecutor`
- **Request Counter**: Thread-safe tracking of requests per file path
- **Rate Limiting**: IP-based rate limiting (5 requests/second) with sliding window algorithm
- **Enhanced Directory Listings**: Shows request statistics for each file
- **Production-Ready**: Proper synchronization and resource management

**Learning Focus:**

- Concurrent programming patterns
- Thread synchronization with locks
- Race condition prevention
- Performance optimization
- Rate limiting algorithms
- Thread pool management

[Read more](http-server-concurrent/README.md)

## Quick Start

### Prerequisites

- Python 3.10+ (Python 3.13+ recommended)
- Docker (optional, for containerized deployment)

### Running the Basic Server

```bash
cd http-server-basic
python3 -m server
```

Visit `http://localhost:8080` in your browser.

### Running the Concurrent Server

```bash
cd http-server-concurrent
python3 -m server --dir-listing enabled
```

Visit `http://localhost:8080` to see request counts in the directory listing.

### Using Docker

Both projects include Docker support:

```bash
cd http-server-basic  # or http-server-concurrent
docker-compose up
```

## Learning Path

These projects are designed to be studied in sequence:

1. **Start with `http-server-basic`**:
   - Understand TCP sockets and HTTP protocol
   - Learn request parsing and response building
   - Implement file serving and directory listings

2. **Progress to `http-server-concurrent`**:
   - Add thread pool for concurrent request handling
   - Implement thread-safe request counting
   - Build a rate limiter with sliding window algorithm
   - Test concurrency and thread safety

## Project Comparison

| Feature | Basic Server | Concurrent Server |
|---------|-------------|-------------------|
| Request Handling | Sequential (one at a time) | Concurrent (thread pool) |
| Request Counter | ❌ | ✅ Thread-safe |
| Rate Limiting | ❌ | ✅ Per-IP, 5 req/sec |
| Performance | ~1 req/sec | ~10+ concurrent req/sec |
| Thread Safety | N/A | ✅ Lock-based |
| Status Codes | 200, 308, 400, 403, 404, 405, 500 | + 429 (Too Many Requests) |
| Directory Listing | ✅ Basic | ✅ With request counts |

## Testing

### Basic Server

```bash
cd http-server-basic
curl http://localhost:8080/
```

### Concurrent Server

The concurrent server includes a comprehensive test suite:

```bash
cd http-server-concurrent
pip install requests  # Required for tests

# Test concurrent performance
python3 test/performance_test.py

# Test rate limiting
python3 test/rate_limit_test.py

# Test thread-safe counter
python3 test/counter_test.py
```

## Concepts Covered

### Network Programming

- TCP socket creation and binding
- Client connection handling
- Socket timeouts and error handling
- Graceful shutdown patterns

### HTTP Protocol

- Request parsing (method, path, headers)
- Response building (status line, headers, body)
- Status codes and error handling
- MIME type detection
- Path normalization and validation

### Concurrency (Concurrent Server)

- Thread pool pattern with `ThreadPoolExecutor`
- Lock-based synchronization (`threading.Lock`)
- Race condition prevention
- Sliding window algorithm for rate limiting
- Thread-safe data structures
- Concurrent vs parallel execution

### Security

- Path traversal attack prevention
- Request size limits
- Rate limiting for DoS protection
- Input validation
- Proper error handling

## Technology Stack

- **Language**: Python 3.13+
- **Core Libraries**:
  - `socket` - TCP networking
  - `threading` - Concurrency (concurrent server)
  - `concurrent.futures` - Thread pool management
  - `pathlib` - File system operations
  - `mimetypes` - Content type detection
- **Testing**: `requests` library for HTTP testing
- **Deployment**: Docker & Docker Compose

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎓 Educational Resources

### HTTP & Networking

- [RFC 9110 - HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [RFC 9112 - HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)
- [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)

### Concurrency

- [MIT 6.102 - Concurrency](https://web.mit.edu/6.102/www/sp25/classes/14-concurrency/)
- [Python Threading Documentation](https://docs.python.org/3/library/threading.html)
- [ThreadPoolExecutor Documentation](https://docs.python.org/3/library/concurrent.futures.html)
