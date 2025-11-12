from pathlib import Path
from typing import Union, Literal
from nbmail.mjml.tags import section, column, text as mjml_text, spacer as mjml_spacer
from nbmail.mjml._core import MJMLTag
from .inline_utils import _is_url, _process_markdown


__all__ = [
    "Block",
    "BlockList",
    "block_text",
    "block_title",
    "block_spacer",
    "block_image",
    "block_plot",
]


class Block:
    """
    Represents a single block component in an email.

    Parameters
    ----------
    mjml_tag
        The underlying MJML section tag
    """

    def __init__(self, mjml_tag: MJMLTag):
        """
        Internal constructor. Users create blocks via `block_*()` functions.

        Parameters
        ----------
        mjml_tag
            The underlying MJML tag
        """
        self._mjml_tag = mjml_tag

    def _to_mjml(self) -> MJMLTag:
        """
        Internal method: retrieve the underlying MJML tag for processing.

        Returns
        -------
        MJMLTag
            The underlying MJML tag structure.
        """
        return self._mjml_tag


class BlockList:
    """
    Container for multiple block components. A block is equivalent to an mj-section.

    Parameters
    ----------
    *args
        One or more Block objects or strings (which will be converted to blocks).

    Examples
    --------
    Users typically create BlockList via the `create_blocks()` function:

    ```python
    from nbmail.compose import create_blocks, block_text, block_title

    content = create_blocks(
        block_title("My Email"),
        block_text("Hello world!")
    )
    ```
    """

    def __init__(self, *args: Union["Block", str]):
        """
        Parameters
        ----------
        *args
            One or more `Block` objects or strings.
        """
        self.sections = list(args)

    def _to_mjml_list(self) -> list[MJMLTag]:
        """
        Internal method: Convert all blocks to MJML tags.

        Used by `compose_email()`.

        Returns
        -------
        list[MJMLTag]
            A list of MJML sections.
        """
        result = []
        for item in self.sections:
            if isinstance(item, Block):
                result.append(item._to_mjml())
            elif isinstance(item, str):
                html = _process_markdown(item)

                # Create a simple text block from the string
                mjml_section = section(
                    column(mjml_text(content=html)), # or mj-raw?
                    # attributes={"padding": "0px"}, # TODO check what happens if we remove this
                )

                result.append(mjml_section)
        return result

    # TODO improve repr to display actual content
    def __repr__(self) -> str:
        return f"<BlockList: {len(self.sections)} sections>"


def block_text(
    text: str, align: Literal["left", "center", "right", "justify"] = "left"
) -> Block:
    """
    Create a block of text (supports Markdown).

    Parameters
    ----------
    text
        Plain text or Markdown. Markdown will be converted to HTML.

    align
        Text alignment. Default is `"left"`.

    Returns
    -------
    Block
        A block containing the formatted text.

    Examples
    --------
    ```python
    from nbmail.compose import block_text

    # Simple text
    block = block_text("Hello world")

    # Markdown text
    block = block_text("This is **bold** and this is *italic*")

    # Centered text
    block = block_text("Centered content", align="center")
    ```
    """
    html = _process_markdown(text)

    mjml_section = section(
        column(
            mjml_text(content=html, attributes={"align": align}),
        ),
        # attributes={"padding": "0px"},
    )

    return Block(mjml_section)


def block_title(
    title: str, align: Literal["left", "center", "right", "justify"] = "center"
) -> Block:
    """
    Create a block of large, emphasized text for headings.

    Parameters
    ----------
    title
        The title text. Markdown will be converted to HTML.
    align
        Text alignment. Default is "center".

    Returns
    -------
    Block
        A block containing the formatted title.

    Examples
    --------
    ```python
    from nbmail.compose import block_title

    # Simple title
    title = block_title("My Newsletter")

    # Centered title (default)
    title = block_title("Welcome!", align="center")
    ```
    """

    html = _process_markdown(title)
    html_wrapped = (
        f'<h1 style="margin: 0; font-size: 32px; font-weight: 300;">{html}</h1>'
    )


    mjml_section = section(
        column(
            mjml_text(
                content=html_wrapped,
                attributes={"align": align},
            )
        ),
        # attributes={"padding": "0px"},
    )

    return Block(mjml_section)


def block_spacer(height: str = "20px") -> Block:
    """
    Insert vertical spacing.

    Parameters
    ----------
    height
        The height of the spacer. Can be any valid CSS height value (e.g., "20px", "2em").
        Default is "20px".

    Returns
    -------
    Block
        A block containing the spacer.

    Examples
    --------
    ```python
    from nbmail.compose import block_spacer, create_blocks, block_text

    email_body = create_blocks(
        block_text("First section"),
        block_spacer("30px"),
        block_text("Second section"),
    )
    ```
    """
    mjml_section = section(
        column(
            mjml_spacer(attributes={"height": height}),
        ),
        # attributes={"padding": "0px"},
    )

    return Block(mjml_section)


def block_image(
    file: str,
    alt: str = "",
    width: Union[int, str] = 520,
    align: Literal["center", "left", "right", "inline"] = "center",
    float: Literal["none", "left", "right"] = "none",
) -> Block:
    """
    Create a block containing an embedded image.

    This function returns a Block with an MJML image tag. For local files, the image 
    bytes are stored and later converted to CID references by `mjml_to_email()`.

    Parameters
    ----------
    file
        Path to local image file or HTTP(S) URL. Local files are automatically
        read and embedded. URLs (http://, https://, or //) are used directly.

    alt
        Alt text for accessibility. Default is empty string.

    width
        Image width. Can be an integer (interpreted as pixels, e.g., 520 → "520px")
        or a CSS string (e.g., "600px", "50%"). Default is 520 (pixels).

    align
        Block-level alignment: "center", "left", "right", or "inline".

    float
        CSS float value for text wrapping: "none", "left", or "right".
        When float is not "none", it takes precedence and wraps content around
        the image.

    Returns
    -------
    Block
        A block containing the image.

    Raises
    ------
    FileNotFoundError
        If a local file path is provided but the file does not exist.

    Examples
    --------
    ```python
    from nbmail.compose import block_image, create_blocks, block_text

    email = compose_email(
        body=create_blocks(
            block_text("Here's an image:"),
            block_image("path/to/image.png", alt="Example", width=600),
            block_text("And some text after it.")
        )
    )
    ```

    Notes
    -----
    - Images from local files are converted to inline attachments with CID references
      during email processing by mjml_to_email().
    - If `float` is not "none", it takes precedence and overrides `align`.
    """    
    # Convert integer width to CSS string
    if isinstance(width, int):
        width_str = f"{width}px"
    else:
        width_str = width

    # Determine alignment style based on float and align parameters
    align_style = ""
    
    # Float takes precedence if not "none"
    if float != "none":
        align_style = f"float: {float};"
    else:
        # Use align parameter if float is "none"
        if align == "center":
            align_style = "display: block; margin: 0 auto;"
        elif align == "left":
            align_style = "display: block; margin: 0;"
        elif align == "right":
            align_style = "display: block; margin: 0 0 0 auto;"
        # "inline" has no special style

    # Detect URL vs local file
    if _is_url(file):
        # For URLs, use as-is
        src = file
    else:
        # For local files, read as bytes for processing by _process_mjml_images
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {file}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file}")
        
        with open(file_path, "rb") as f:
            src = f.read()

    attrs = {
        "src": src,
        "alt": alt,
        "width": width_str,
    }
    
    if align_style:
        attrs["style"] = f"{align_style} max-width: 100%; height: auto;"
    else:
        attrs["style"] = "max-width: 100%; height: auto;"

    image_tag = MJMLTag("mj-image", attributes=attrs, _is_leaf=True)
    mjml_section = section(column(image_tag))
    
    return Block(mjml_section)


def block_plot(
    fig,
    alt: str = "",
    width: Union[int, str] = 520,
    align: Literal["center", "left", "right", "inline"] = "center",
    float: Literal["none", "left", "right"] = "none",
) -> Block:
    """
    Create a block containing an embedded plotnine plot.

    This function saves a plotnine plot to a temporary PNG file and wraps it as a Block
    with an embedded image.

    Parameters
    ----------
    fig
        A plotnine plot object (ggplot).

    alt
        Alt text for accessibility. Default is empty string.

    width
        Image width. Can be an integer (interpreted as pixels, e.g., 520 → "520px")
        or a CSS string (e.g., "600px", "50%"). Default is 520 (pixels).

    align
        Block-level alignment: "center", "left", "right", or "inline".
        Default is "center".

    float
        CSS float value for text wrapping: "none", "left", or "right".
        Default is "none".

    Returns
    -------
    Block
        A block containing the plot image.

    Raises
    ------
    ImportError
        If the plotnine package is not installed.

    Examples
    --------
    ```python
    from nbmail.compose import block_plot, create_blocks, block_text
    from plotnine import ggplot, aes, geom_point, mtcars

    plot = (
        ggplot(mtcars, aes("disp", "hp"))
        + geom_point()
    )

    email = compose_email(
        body=create_blocks(
            block_text("Here's my plot:"),
            block_plot(plot, alt="Scatter plot"),
            block_text("What do you think?")
        )
    )
    ```
    """
    import tempfile
    from pathlib import Path
    import importlib.util

    if importlib.util.find_spec("plotnine") is None:
        raise ImportError(
            "The 'plotnine' package is required for plot embedding. "
            "Install it with: pip install plotnine"
        )

    # Create a temporary PNG file
    tmpfile = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmpfile_path = tmpfile.name
    tmpfile.close()

    try:
        fig.save(tmpfile_path, dpi=200, verbose=False)

        img_block = block_image(
            file=tmpfile_path,
            alt=alt,
            width=width,
            align=align,
            float=float,
        )

        return img_block

    finally:
        Path(tmpfile_path).unlink(missing_ok=True)

