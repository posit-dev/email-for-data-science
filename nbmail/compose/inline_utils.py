import base64
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional

import re

__all__ = [
    "md",
    "add_cta_button",
    "add_readable_time",
]


def _process_markdown(content: Optional[str]) -> Optional[str]:
    """
    Convert Markdown text to HTML (internal utility).

    Used internally by block functions. For public use, call `md()` instead.

    Parameters
    ----------
    content
        Markdown text to convert. If None, returns None.

    Returns
    -------
    str or None
        HTML representation of the Markdown, or None if content is None.
    """
    if content is None:
        return None

    try:
        import markdown
    except ImportError:
        raise ImportError(
            "The 'markdown' package is required for Markdown processing. "
            "Install it with: pip install markdown"
        )

    html = markdown.markdown(content, extensions=["extra", "codehilite", "toc"])
    return html


def md(text: str) -> str:
    """
    Process Markdown text to HTML.

    Public utility function for converting Markdown strings to HTML.

    Parameters
    ----------
    text
        Markdown text to convert.

    Returns
    -------
    str
        HTML representation of the Markdown.

    Examples
    --------
    ```{python}
    from nbmail.compose import md, block_text, compose_email

    html = md("This is **bold** and this is *italic*")

    # Use in a block
    compose_email(body=block_text(html))
    ```
    """
    return _process_markdown(text)


def _is_url(file: str) -> bool:
    """
    Detect if the file parameter is a URL (HTTP/HTTPS) or protocol-relative URL.

    Parameters
    ----------
    file
        The file path or URL string to test.

    Returns
    -------
    bool
        True if file is a URL (http://, https://, or //), False otherwise.
    """
    pattern = r"^(https?:)?//"
    return bool(re.match(pattern, file, re.IGNORECASE))


def _guess_mime_type(file: str) -> str:
    """
    Guess MIME type from file extension.

    Parameters
    ----------
    file
        File path or URL.

    Returns
    -------
    str
        MIME type string (e.g., "image/png", "image/jpeg").
        Defaults to "image/png" if type cannot be determined.
    """
    mime_type, _ = mimetypes.guess_type(file)
    return mime_type or "image/png"


def _read_local_file_as_data_uri(file: str) -> str:
    """
    Read a local file and convert to data URI with base64 encoding.

    Parameters
    ----------
    file
        Path to local file.

    Returns
    -------
    str
        Data URI string (e.g., "data:image/png;base64,iVBORw0KG...").

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    IOError
        If the file cannot be read.
    """
    file_path = Path(file)

    if not file_path.exists():
        raise FileNotFoundError(f"Image file not found: {file}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file}")

    # Read file as binary
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # Encode to base64
    b64_string = base64.b64encode(file_bytes).decode("utf-8")

    # Guess MIME type
    mime_type = _guess_mime_type(str(file_path))

    return f"data:{mime_type};base64,{b64_string}"


def add_cta_button(
    label: str,
    url: str,
    bg_color: str = "#007bff",
    text_color: str = "#ffffff",
) -> str:
    """
    Create a call-to-action button.

    Parameters
    ----------
    label
        Button text.

    url
        Target URL.

    bg_color
        Button background color (hex). Default is `"#007bff"`.

    text_color
        Button text color (hex). Default is `"#ffffff"`.

    Returns
    -------
    str
        HTML button element that can be embedded in emails.

    Examples
    --------
    ```{python}
    from nbmail.compose import add_cta_button, block_text, compose_email

    button_html = add_cta_button("Learn More", "https://example.com")

    compose_email(
        body=block_text(f"Ready?\\n\\n{button_html}")
    )
    ```
    """
    button_html = (
        f'<a href="{url}" style="display: inline-block; '
        f"padding: 12px 24px; "
        f"background-color: {bg_color}; "
        f"color: {text_color}; "
        f"text-decoration: none; "
        f"border-radius: 4px; "
        f"font-weight: bold; "
        f'text-align: center;">{label}</a>'
    )
    return button_html


def add_readable_time(
    dt: datetime,
    format_str: str = "%B %d, %Y",
) -> str:
    """
    Format a datetime as readable text.

    Parameters
    ----------
    dt
        Datetime object to format.

    format_str
        Python strftime format string. Default is "%B %d, %Y" (e.g., "November 10, 2025").

    Returns
    -------
    str
        Formatted date/time string.

    Raises
    ------
    TypeError
        If dt is not a datetime object.

    Examples
    --------
    ```{python}
    from datetime import datetime
    from nbmail.compose import add_readable_time, block_text, compose_email

    time_str = add_readable_time(datetime.now())

    compose_email(
        body=block_text(f"Report generated: {time_str}")
    )
    ```
    """
    if not isinstance(dt, datetime):
        raise TypeError(f"Expected datetime object, got {type(dt).__name__}")

    return dt.strftime(format_str)
