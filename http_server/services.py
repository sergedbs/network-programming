"""File serving services - Static file resolution and content type detection."""

from pathlib import Path
import mimetypes


class StaticFileService:
    """Resolves safe file paths and determines content types."""

    def __init__(self, base_dir: str = "public", allow_directory: bool = False):
        self.base_dir = Path(base_dir).resolve()
        self.allow_directory = allow_directory

    def resolve(self, request_path: str) -> Path | None:
        relative = request_path.lstrip("/")
        target = (self.base_dir / relative).resolve()
        try:
            target.relative_to(self.base_dir)
        except ValueError:
            return None  # path traversal attempt
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
