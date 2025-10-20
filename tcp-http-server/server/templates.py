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
                return template_path.read_text(encoding="utf-8")

        # Fallback to inline templates
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
        return template.format(
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

        # Generate breadcrumbs
        breadcrumbs = self._generate_breadcrumbs(path)

        # Generate entry rows HTML
        entry_rows = self._generate_entry_rows(entries)

        return template.format(
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
            return '<tr><td colspan="4" class="empty">Empty directory</td></tr>'

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

            row = f"""
                <tr class="{entry_type}">
                    <td class="icon">{icon}</td>
                    <td class="name"><a href="{entry["path"]}">{entry["name"]}</a></td>
                    <td class="size">{size}</td>
                    <td class="modified">{modified}</td>
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
        """Get inline template as fallback."""
        templates = {
            "error": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{status_code} {status_text}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 60px 40px;
            max-width: 600px;
            text-align: center;
        }}
        .status-code {{
            font-size: 120px;
            font-weight: 700;
            color: #667eea;
            line-height: 1;
            margin-bottom: 20px;
        }}
        h1 {{
            font-size: 32px;
            color: #333;
            margin-bottom: 20px;
        }}
        .message {{
            font-size: 18px;
            color: #666;
            margin-bottom: 40px;
            line-height: 1.6;
        }}
        .server-info {{
            font-size: 14px;
            color: #999;
            padding-top: 30px;
            border-top: 1px solid #eee;
        }}
        a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="status-code">{status_code}</div>
        <h1>{status_text}</h1>
        <p class="message">{message}</p>
        <a href="/">← Back to Home</a>
        <div class="server-info">{server_name}</div>
    </div>
</body>
</html>""",
            "directory": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index of {path}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .breadcrumbs {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .breadcrumbs a {{
            color: white;
            text-decoration: none;
            padding: 5px;
            border-radius: 4px;
            transition: background 0.2s;
        }}
        .breadcrumbs a:hover {{
            background: rgba(255,255,255,0.2);
        }}
        .info {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
            font-size: 14px;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        thead {{
            background: #f8f9fa;
            border-bottom: 2px solid #e0e0e0;
        }}
        th {{
            padding: 15px 30px;
            text-align: left;
            font-weight: 600;
            color: #333;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 15px 30px;
            border-bottom: 1px solid #f0f0f0;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .directory {{
            background: #fafafa;
        }}
        .icon {{
            width: 40px;
            font-size: 20px;
        }}
        .name a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        .name a:hover {{
            text-decoration: underline;
        }}
        .size {{
            color: #666;
            width: 120px;
        }}
        .modified {{
            color: #999;
            width: 200px;
            font-size: 14px;
        }}
        .empty {{
            text-align: center;
            color: #999;
            padding: 60px;
            font-style: italic;
        }}
        footer {{
            padding: 20px 30px;
            text-align: center;
            color: #999;
            font-size: 14px;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Index of {path}</h1>
            <div class="breadcrumbs">{breadcrumbs}</div>
        </header>
        <div class="info">
            {entry_count} items
        </div>
        <table>
            <thead>
                <tr>
                    <th></th>
                    <th>Name</th>
                    <th>Size</th>
                    <th>Modified</th>
                </tr>
            </thead>
            <tbody>
{entry_rows}
            </tbody>
        </table>
        <footer>{server_name}</footer>
    </div>
</body>
</html>""",
        }
        return templates.get(name, "")
