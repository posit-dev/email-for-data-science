from typing import Union
from nbmail.mjml.tags import section, column, text as mjml_text, spacer as mjml_spacer
from nbmail.mjml._core import MJMLTag
from .inline_utils import _process_markdown
from typing import Literal


__all__ = [
    "Block",
    "BlockList",
    "block_text",
    "block_title",
    "block_spacer",
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
