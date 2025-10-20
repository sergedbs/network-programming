"""File serving services - Static file resolution and content type detection."""

from pathlib import Path
import mimetypes


def is_safe_path(target: Path, base: Path) -> bool:
    """Check if target path is within base directory (prevents path traversal)."""
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def format_file_size(size_bytes: int) -> str:
    """Format bytes as human-readable size (e.g., 1.2 KB, 3.4 MB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


class StaticFileService:
    """Resolves safe file paths and determines content types."""

    def __init__(self, base_dir: str = "public", allow_directory: bool = False):
        self.base_dir = Path(base_dir).resolve()
        self.allow_directory = allow_directory

    def resolve(self, request_path: str) -> Path | None:
        relative = request_path.lstrip("/")
        target = (self.base_dir / relative).resolve()

        # Check for path traversal attack
        if not is_safe_path(target, self.base_dir):
            return None

        if not target.exists():
            return None

        if target.is_file():
            return target

        if self.allow_directory and target.is_dir():
            return target

        return None

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def content_type(self, path: Path) -> str:
        mimetype, _ = mimetypes.guess_type(str(path))
        return mimetype or "application/octet-stream"

    def list_directory(self, directory: Path) -> list[dict]:
        """
        List directory contents with metadata.

        Args:
            directory: Directory path to list

        Returns:
            List of dictionaries with entry metadata:
            [
                {
                    "name": "file.txt",
                    "type": "file" or "directory",
                    "size": 1024,  # bytes, None for directories
                    "size_formatted": "1.0 KB",
                    "modified": "2025-10-20 12:30:45",
                    "path": "/subdir/file.txt"
                },
                ...
            ]
        """
        if not directory.is_dir():
            return []

        entries = []

        # Add parent directory link if not at root
        try:
            relative = directory.relative_to(self.base_dir)
            if str(relative) != ".":
                parent_path = "/" + str(relative.parent).replace("\\", "/")
                if parent_path.endswith("/."):
                    parent_path = "/"
                entries.append(
                    {
                        "name": "..",
                        "type": "directory",
                        "size": None,
                        "size_formatted": "-",
                        "modified": "-",
                        "path": parent_path,
                    }
                )
        except ValueError:
            pass

        # List all entries in directory
        try:
            items = sorted(
                directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
            )
        except PermissionError:
            return entries

        for item in items:
            # Skip hidden files (starting with .)
            if item.name.startswith("."):
                continue

            # Calculate relative path for URL
            try:
                rel_path = item.relative_to(self.base_dir)
                url_path = "/" + str(rel_path).replace("\\", "/")
                if item.is_dir():
                    url_path += "/"
            except ValueError:
                continue

            # Get file metadata
            try:
                stat = item.stat()
                modified = self._format_timestamp(stat.st_mtime)

                if item.is_file():
                    size = stat.st_size
                    size_formatted = format_file_size(size)
                    entry_type = "file"
                else:
                    size = None
                    size_formatted = "-"
                    entry_type = "directory"

                entries.append(
                    {
                        "name": item.name,
                        "type": entry_type,
                        "size": size,
                        "size_formatted": size_formatted,
                        "modified": modified,
                        "path": url_path,
                    }
                )
            except (OSError, PermissionError):
                # Skip files we can't read
                continue

        return entries

    def _format_timestamp(self, timestamp: float) -> str:
        """Format Unix timestamp as human-readable string."""
        from datetime import datetime

        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
