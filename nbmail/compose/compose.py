from typing import Optional, Union

from nbmail.ingress import mjml_to_email
from nbmail.structs import Email
from nbmail.mjml.tags import (
    mjml,
    body as mj_body,  # to not confuse with body arg
    head,
    mj_attributes,
    mj_all,
    section,
    column,
)
from nbmail.mjml._core import MJMLTag
from .blocks import Block, BlockList, block_title

__all__ = [
    "compose_email",
    "create_blocks",
]


def create_blocks(*args: Union[Block, str]) -> BlockList:
    """
    Group block components for use in compose_email().

    Collects multiple `block_*()` function calls into a renderable structure.

    Parameters
    ----------
    *args
        One or more block_*() calls or strings.

    Returns
    -------
    BlockList
        Container for blocks, renderable to email content.

    Examples
    --------
    ```python
    from nbmail.compose import create_blocks, block_text, block_title, block_spacer

    content = create_blocks(
        block_title("Welcome!"),
        block_text("This is the main content."),
        block_spacer("20px"),
        block_text("Thanks for reading!")
    )
    ```
    """
    return BlockList(*args)


def compose_email(
    body: Optional[Union[str, Block, BlockList]] = None,
    header: Optional[Union[str, Block, BlockList]] = None,
    footer: Optional[Union[str, Block, BlockList]] = None,
    title: Optional[str] = None,
    template: str = "blastula",
    **kwargs,
) -> Email:
    """
    Compose an email message using simple building blocks or Markdown.

    This is the primary entry point for creating emails in nbmail. It accepts
    optional header, body, and footer sections, processes them into MJML,
    and returns an `Email` object ready for preview or sending.

    Parameters
    ----------
    body
        Main email content. Can be a Markdown string, single Block, or `blocks()` result.

    header
        Optional header section (appears at top).

    footer
        Optional footer section (appears at bottom).

    title
        Large title/header text to display at the top of the email.
        If provided, this creates a `block_title()` in the header section.
        Note: This is NOT the email subject line; use email metadata for that.

    template
        Email template style. Default is "blastula", which wraps content in a grey
        border container (similar to Blastula's `html_email_template_1`).
        Use `"none"` for no template wrapper.

    **kwargs
        Additional template options (reserved for future use).

    Returns
    -------
    Email
        Converted Email object ready for preview or sending.

    Examples
    --------
    Simple email with single block:

    ```python
    from nbmail.compose import compose_email, block_text

    email = compose_email(
        body=block_text("This is a simple email.")
    )
    ```

    Email with title/header and multiple blocks:

    ```python
    from nbmail.compose import compose_email, create_blocks, block_title, block_text

    email = compose_email(
        title="Welcome!",  # Creates a large title block at top
        body=create_blocks(
            block_text("Welcome to this week's update!"),
            block_text("Here's what's new...")
        )
    )
    ```

    Email with header section and body:

    ```python
    from nbmail.compose import compose_email, create_blocks, block_title, block_text

    email = compose_email(
        header=create_blocks(block_title("Newsletter")),
        body=create_blocks(
            block_text("Welcome to this week's update!"),
            block_text("Here's what's new...")
        ),
        footer=create_blocks(block_text("© 2025 My Company"))
    )
    ```

    Email with embedded images:

    ```python
    from nbmail.compose import compose_email, add_image, block_text, md

    img_html = add_image("path/to/image.png", alt="Product image", width="500px")
    email = compose_email(
        title="Product Feature",
        body=block_text(md(f"Check this out:\\n\\n{img_html}"))
    )
    ```
    """
    # Convert sections (header, body, footer) to MJML lists
    header_mjml_list = _section_to_mjml_list(header)
    body_mjml_list = _section_to_mjml_list(body)
    footer_mjml_list = _section_to_mjml_list(footer)

    # If title is provided, prepend it to header
    if title:
        title_block_mjml = block_title(title)._to_mjml()
        header_mjml_list = [title_block_mjml] + header_mjml_list

    # Apply template wrapper if requested
    if template == "blastula":
        all_sections = _apply_blastula_template(
            header_mjml_list, body_mjml_list, footer_mjml_list
        )
    elif template == "none":
        # Combine all sections without template
        all_sections = header_mjml_list + body_mjml_list + footer_mjml_list
    else:
        raise ValueError(f"Unknown template: {template}. Use 'blastula' or 'none'.")

    # Build full MJML email structure with head containing spacing defaults (padding: 0px)
    email_structure = mjml(
        head(
            mj_attributes(
                mj_all(attributes={"padding": "0px"}),
                section(attributes={"padding": "0px"}),
            ),
        ),
        mj_body(
            *all_sections,
            attributes={"width": "600px"},  # TODO check what happens if we remove this
        ),
    )

    email_obj = mjml_to_email(email_structure)

    return email_obj


def _section_to_mjml_list(section: Optional[Union[str, Block, BlockList]]):
    """
    Convert a section (string, Block, BlockList, or None) to a list of MJML tags.

    Internal helper for `compose_email()`.

    Parameters
    ----------
    section
        The section content to convert.

    Returns
    -------
    list[MJMLTag]
        A list of MJML tag structures (empty if section is None).
    """
    if section is None:
        return []

    elif isinstance(section, Block):
        # Auto-wrap single Block in BlockList
        return [section._to_mjml()]

    elif isinstance(section, BlockList):
        return section._to_mjml_list()

    elif isinstance(section, str):
        # Convert string to BlockList and then to MJML
        block_list = BlockList(section)
        return block_list._to_mjml_list()

    else:
        raise TypeError(
            f"Expected str, Block, BlockList, or None, got {type(section).__name__}"
        )


def _apply_blastula_template(
    header_sections: list, body_sections: list, footer_sections: list
):
    """
    Apply Blastula-style template with grey border around body content.

    This creates a three-part layout:\n
    - Header sections with grey background at top
    - Body sections wrapped in a white box with grey border/padding around it
    - Footer sections with grey background at bottom

    All three parts together form a unified visual container with the body
    content highlighted in white against the grey border.

    Parameters
    ----------
    header_sections
        MJML sections for the header (styled with grey background).

    body_sections
        MJML sections for the main content (wrapped in white box with grey border).

    footer_sections
        MJML sections for the footer (styled with grey background).

    Returns
    -------
    list[MJMLTag]
        Styled sections: header + wrapped_body + footer.
    """
    # Apply grey background to header sections
    grey_attrs = {
        "background-color": "#f6f6f6",
        "padding-right": "16px",
        "padding-left": "16px",
    }
    styled_header = [
        _apply_section_attributes(section, grey_attrs) for section in header_sections
    ]

    # Wrap body sections in a white box with grey border/padding
    body_wrapper = section(
        column(
            *body_sections,
            attributes={
                "background-color": "white",
                "padding": "0px",
            },
        ),
        attributes={
            "background-color": "#f6f6f6",  # Grey background creates the "border" effect
            "padding": "16px",
        },
    )

    # Apply grey background to footer sections
    styled_footer = [
        _apply_section_attributes(section, grey_attrs) for section in footer_sections
    ]

    return styled_header + [body_wrapper] + styled_footer


def _apply_section_attributes(section: MJMLTag, attributes: dict) -> MJMLTag:
    """
    Apply or merge attributes to a section tag.

    Internal helper for `_apply_blastula_template()`.

    Parameters
    ----------
    section
        The section tag to modify.

    attributes
        Attributes to apply or merge.

    Returns
    -------
    MJMLTag
        A new section tag with merged attributes.
    """
    merged_attrs = {**(section.attrs or {}), **attributes}
    section.attrs = merged_attrs
    return section
