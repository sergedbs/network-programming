"""Template service for rendering HTML pages."""

from pathlib import Path
from typing import Any


class TemplateService:
    """Service for loading and rendering HTML templates."""

    def __init__(self, template_dir: Path | None = None):
        """
        Initialize template service.

        Args:
            template_dir: Directory containing template files. If None, uses inline templates.
        """
        self.template_dir = template_dir
        if template_dir and template_dir.exists():
            self._use_files = True
        else:
            self._use_files = False

    def load_template(self, name: str) -> str:
        """
        Load template from file or return inline version.

        Args:
            name: Template name (without .html extension)

        Returns:
            Template content as string
        """
        if self._use_files:
            template_path = self.template_dir / f"{name}.html"
            if template_path.exists():
                try:
                    return template_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    pass

        return self._get_inline_template(name)

    def render_error(
        self, status_code: int, status_text: str, message: str, server_name: str
    ) -> str:
        """
        Render error page.

        Args:
            status_code: HTTP status code (e.g., 404)
            status_text: Status text (e.g., "Not Found")
            message: Detailed error message
            server_name: Server identifier

        Returns:
            Rendered HTML as string
        """
        template = self.load_template("error")
        try:
            return template.format(
                status_code=status_code,
                status_text=status_text,
                message=message,
                server_name=server_name,
            )
        except (KeyError, ValueError):
            fallback = self._get_inline_template("error")
            return fallback.format(
                status_code=status_code,
                status_text=status_text,
                message=message,
                server_name=server_name,
            )

    def render_directory(
        self, path: str, entries: list[dict[str, Any]], server_name: str
    ) -> str:
        """
        Render directory listing page.

        Args:
            path: Current directory path (URL path)
            entries: List of directory entries with metadata
            server_name: Server identifier

        Returns:
            Rendered HTML as string
        """
        template = self.load_template("directory")

        breadcrumbs = self._generate_breadcrumbs(path)
        entry_rows = self._generate_entry_rows(entries)

        try:
            return template.format(
                path=path,
                breadcrumbs=breadcrumbs,
                entry_rows=entry_rows,
                server_name=server_name,
                entry_count=len(entries),
            )
        except (KeyError, ValueError):
            fallback = self._get_inline_template("directory")
            return fallback.format(
                path=path,
                breadcrumbs=breadcrumbs,
                entry_rows=entry_rows,
                server_name=server_name,
                entry_count=len(entries),
            )

    def _generate_breadcrumbs(self, path: str) -> str:
        """Generate breadcrumb navigation HTML."""
        parts = [p for p in path.split("/") if p]
        if not parts:
            return '<a href="/">Home</a>'

        crumbs = ['<a href="/">Home</a>']
        current_path = ""

        for part in parts:
            current_path += f"/{part}"
            crumbs.append(f'<a href="{current_path}">{part}</a>')

        return " / ".join(crumbs)

    def _generate_entry_rows(self, entries: list[dict[str, Any]]) -> str:
        """Generate table rows for directory entries."""
        if not entries:
            return '<tr><td colspan="5" class="empty">Empty directory</td></tr>'

        rows = []
        for entry in entries:
            entry_type = entry["type"]
            icon = (
                "📁"
                if entry_type == "directory"
                else self._get_file_icon(entry["name"])
            )
            size = entry.get("size_formatted", "-")
            modified = entry.get("modified", "-")
            request_count = entry.get("request_count", 0)

            row = f"""
                <tr class="{entry_type}">
                    <td class="icon">{icon}</td>
                    <td class="name"><a href="{entry["path"]}">{entry["name"]}</a></td>
                    <td class="size">{size}</td>
                    <td class="modified">{modified}</td>
                    <td class="requests">{request_count}</td>
                </tr>"""
            rows.append(row)

        return "\n".join(rows)

    def _get_file_icon(self, filename: str) -> str:
        """Get icon emoji for file based on extension."""
        ext = Path(filename).suffix.lower()
        icons = {
            ".html": "📄",
            ".htm": "📄",
            ".css": "🎨",
            ".js": "📜",
            ".json": "📋",
            ".xml": "📋",
            ".txt": "📝",
            ".md": "📝",
            ".pdf": "📕",
            ".doc": "📘",
            ".docx": "📘",
            ".xls": "📗",
            ".xlsx": "📗",
            ".png": "🖼️",
            ".jpg": "🖼️",
            ".jpeg": "🖼️",
            ".gif": "🖼️",
            ".svg": "🖼️",
            ".mp3": "🎵",
            ".wav": "🎵",
            ".mp4": "🎬",
            ".avi": "🎬",
            ".zip": "📦",
            ".tar": "📦",
            ".gz": "📦",
            ".py": "🐍",
            ".java": "☕",
            ".c": "©️",
            ".cpp": "©️",
            ".h": "©️",
        }
        return icons.get(ext, "📄")

    def _get_inline_template(self, name: str) -> str:
        """Get minimal inline template as fallback (no styling)."""
        templates = {
            "error": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{status_code} {status_text}</title>
</head>
<body>
    <h1>{status_code} {status_text}</h1>
    <p>{message}</p>
    <hr>
    <p><a href="/">Back to Home</a></p>
    <footer><small>{server_name}</small></footer>
</body>
</html>""",
            "directory": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index of {path}</title>
</head>
<body>
    <h1>Index of {path}</h1>
    <p>{breadcrumbs}</p>
    <hr>
    <p>{entry_count} items</p>
    <table border="1" cellpadding="5" cellspacing="0">
        <thead>
            <tr>
                <th>Icon</th>
                <th>Name</th>
                <th>Size</th>
                <th>Modified</th>
            </tr>
        </thead>
        <tbody>
{entry_rows}
        </tbody>
    </table>
    <hr>
    <footer><small>{server_name}</small></footer>
</body>
</html>""",
        }
        return templates.get(name, "")
