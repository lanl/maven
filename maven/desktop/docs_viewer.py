"""Help > Documentation menu: renders the project's root-level markdown docs
(Installable_Readme.md, Database_Migrations.md) as HTML in their own native
window, instead of dumping raw markdown on the user or shelling out to
whatever the OS has registered for .md files."""
import markdown
import webview

from maven.desktop.paths import get_doc_path
from maven.desktop.wrapper_log import get_logger

logger = get_logger("docs_viewer")

_PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    max-width: 860px;
    margin: 2rem auto;
    padding: 0 1.5rem 3rem;
    line-height: 1.6;
    color: #1a1a1a;
  }}
  h1, h2, h3 {{ border-bottom: 1px solid #e1e4e8; padding-bottom: 0.3rem; }}
  code {{ background: #f3f3f3; padding: 0.15em 0.35em; border-radius: 3px; font-size: 0.9em; }}
  pre {{ background: #f6f8fa; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
  pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #e1e4e8; padding: 0.5em 0.8em; text-align: left; }}
  th {{ background: #f6f8fa; }}
  a {{ color: #0366d6; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def _render(filename, title):
    source_path = get_doc_path(filename)
    text = source_path.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    return _PAGE_TEMPLATE.format(title=title, body=body)


def open_doc_window(window, filename, title):
    try:
        html = _render(filename, title)
    except Exception as exc:
        logger.error("Could not load documentation %s: %s", filename, exc)
        window.create_confirmation_dialog("Could not open documentation", str(exc))
        return
    webview.create_window(title, html=html, width=900, height=800)
    logger.info("Opened documentation window: %s", filename)
