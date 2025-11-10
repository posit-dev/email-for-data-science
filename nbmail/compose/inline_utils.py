# import base64
# from datetime import datetime
# from pathlib import Path
from typing import Optional

__all__ = [
    "md",
    "add_image",
    "add_plot",
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
    Can include images created via `add_image()` or `add_plot()`.

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
    ```python
    from nbmail.compose import md, block_text

    # Simple markdown
    html = md("This is **bold** and this is *italic*")

    # With embedded image
    img_html = add_image("path/to/image.png")
    html = md(f"Check this out!\\n\\n{img_html}")

    # Use in a block
    email = compose_email(body=block_text(html))
    ```
    """
    return _process_markdown(text)


def add_image(
    src: str,
    alt: str = "",
    width: str = "520px",
    align: str = "center",
) -> str:
    """
    Create HTML img tag for embedding images.

    Parameters
    ----------
    src
        URL or path to image file.

    alt
        Alt text for accessibility. Default is empty string.

    width
        Image width (e.g., `"520px"`)

    align
        Image alignment.

    Returns
    -------
    str
        HTML img tag that can be embedded in Markdown or passed to `block_text()`.

    Examples
    --------
    ```python
    from nbmail.compose import add_image, block_text, compose_email

    # From URL
    img_html = add_image("https://example.com/image.png", alt="Example image")

    # From local file
    img_html = add_image("path/to/image.png", alt="My image", width="600px")

    # Use in email
    email = compose_email(
        body=block_text(f"Check this out:\\n{img_html}")
    )
    ```
    """
    # Determine alignment style
    align_style = ""
    if align == "center":
        align_style = "display: block; margin: 0 auto;"
    elif align == "left":
        align_style = "display: block; margin: 0;"
    elif align == "right":
        align_style = "float: right;"
    # "inline" has no special style

    # Create img tag
    img_tag = (
        f'<img src="{src}" alt="{alt}" width="{width}" '
        f'style="{align_style} max-width: 100%; height: auto;" />'
    )

    return img_tag


def add_plot(
    fig,
    alt: str = "",
    width: str = "520px",
) -> str:
    """
    Convert a plot figure to embedded HTML img tag.

    Parameters
    ----------
    fig
        Plot figure object. Supports matplotlib.figure.Figure and plotly.graph_objects.Figure.

    alt
        Alt text for accessibility. Default is empty string.

    width
        Image width (e.g., "520px"). Default is "520px".

    Returns
    -------
    str
        HTML img tag with base64-encoded plot that can be embedded in emails.

    Examples
    --------
    ```python
    from nbmail.compose import add_plot, block_text, compose_email
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])

    plot_html = add_plot(fig, alt="Sales trends", width="600px")

    email = compose_email(
        body=block_text(f"Here's the trend:\\n{plot_html}")
    )
    ```
    """
    return NotImplementedError("Coming soon.")


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
    ```python
    from nbmail.compose import add_cta_button, block_text, compose_email

    button_html = add_cta_button("Learn More", "https://example.com")

    email = compose_email(
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
    dt,
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

    Examples
    --------
    ```python
    from datetime import datetime
    from nbmail.compose import add_readable_time, block_text, compose_email

    time_str = add_readable_time(datetime.now())
    # Output: "November 10, 2025"

    # Custom format
    time_str = add_readable_time(datetime.now(), format_str="%A, %B %d")
    # Output: "Sunday, November 10"

    email = compose_email(
        body=block_text(f"Report generated: {time_str}")
    )
    ```
    """
    raise NotImplementedError("Coming soon.")

    # if not isinstance(dt, datetime):
    #     raise TypeError(f"Expected datetime object, got {type(dt).__name__}")

    # return dt.strftime(format_str)
