FROM python:3.13-slim-bookworm

WORKDIR /app

# Copy server code
COPY server/ /app/server/

# Copy content to serve
COPY public/ /app/public/

# Expose port
EXPOSE 8080

# Run server
CMD ["python3", "-m", "server"]