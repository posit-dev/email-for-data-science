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
    wrapper,
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
    ```{python}
    from nbmail.compose import create_blocks, block_text, block_title, block_spacer

    create_blocks(
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

    ```{python}
    from nbmail.compose import compose_email, block_text

    compose_email(
        body=block_text("This is a simple email.")
    )
    ```

    Email with title/header and multiple blocks:

    ```{python}
    from nbmail.compose import compose_email, create_blocks, block_title, block_text

    compose_email(
        title="Welcome!",
        body=block_text("Welcome to this week's update!"),
    )
    ```

    Email with header section and body:

    ```{python}
    from nbmail.compose import compose_email, create_blocks, block_title, block_text

    compose_email(
        header=create_blocks(block_title("Newsletter")),
        body=create_blocks(
            block_text("Welcome to this week's update!"),
            block_text("Here's what's new...")
        ),
        footer=create_blocks(block_text("© 2025 My Company"))
    )
    ```
    """
    header_mjml_list = _component_to_mjml_section(header)
    body_mjml_list = _component_to_mjml_section(body)
    footer_mjml_list = _component_to_mjml_section(footer)

    # If title is provided, prepend it to header
    if title:
        title_block_mjml = block_title(title)._to_mjml()
        header_mjml_list = [title_block_mjml] + header_mjml_list

    if template == "blastula":
        all_sections = _apply_blastula_template(
            header_mjml_list, body_mjml_list, footer_mjml_list
        )
    elif template == "none":
        all_sections = header_mjml_list + body_mjml_list + footer_mjml_list
    else:
        raise ValueError(f"Unknown template: {template}. Use 'blastula' or 'none'.")

    # Build full MJML email structure
    email_structure = mjml(
        head(
            mj_attributes(
                mj_all(
                    attributes={
                        "padding": "0px",
                        "font-family": "Helvetica, sans-serif",
                        "font-size": "14px",
                    }
                ),
            ),
        ),
        mj_body(
            *all_sections,
            attributes={"width": "600px", "background-color": "#f6f6f6"},
        ),
    )

    email_obj = mjml_to_email(email_structure)

    return email_obj


def _component_to_mjml_section(
    component: Optional[Union[str, Block, BlockList]],
) -> list[MJMLTag]:
    """
    Convert a component (string, Block, BlockList, or None) to a list of MJML tags.

    Internal helper for `compose_email()`.

    Parameters
    ----------
    component
        The component content to convert.

    Returns
    -------
    list[MJMLTag]
        A list of MJML sections (empty if component is None).
    """
    if component is None:
        return []

    elif isinstance(component, Block):
        # Auto-wrap single Block in BlockList
        return [component._to_mjml()]

    elif isinstance(component, BlockList):
        return component._to_mjml_list()

    elif isinstance(component, str):
        block_list = BlockList(component)
        return block_list._to_mjml_list()

    else:
        raise TypeError(
            f"Expected str, Block, BlockList, or None, got {type(section).__name__}"
        )


def _apply_blastula_template(
    header_sections: list[MJMLTag],
    body_sections: list[MJMLTag],
    footer_sections: list[MJMLTag],
) -> list[MJMLTag]:
    """
    Apply Blastula-style template with grey border around body content.

    Returns
    -------
    list[MJMLTag]
        Styled sections: header + wrapped_body + footer.
    """
    section_attrs = {
        "background-color": "#f6f6f6",
        "padding": "0px 20px",
    }
    text_attrs = {
        "font-size": "12px",
        "color": "#999999",
        "align": "center",
    }

    def apply_blastula_styles(sections: list[MJMLTag]) -> list[MJMLTag]:
        """Apply section-level and text-level attributes."""
        result = [
            _apply_attributes(s, tag_names=None, attributes=section_attrs)
            for s in sections
        ]
        return [
            _apply_attributes(s, tag_names=["mj-text"], attributes=text_attrs)
            for s in result
        ]

    # Apply attributes to body sections
    styled_body = [
        _apply_attributes(
            section,
            tag_names=None,
            attributes={
                "background-color": "white",
                "padding": "0px 10px",
            },
        )
        for section in body_sections
    ]

    body_wrapper = wrapper(
        *styled_body,
        attributes={
            "background-color": "#f6f6f6",
            "padding": "10px",
        },
    )

    return (
        apply_blastula_styles(header_sections)
        + [body_wrapper]
        + apply_blastula_styles(footer_sections)
    )


def _apply_attributes(
    tag: MJMLTag, tag_names: Optional[list[str]], attributes: dict
) -> MJMLTag:
    """
    Recursively apply attributes to tags matching specified names.

    If tag_names is None, applies attributes to the top-level tag itself.
    If tag_names is a list, applies attributes only to matching tags within children.

    Internal helper for applying attributes to MJML structures.

    Parameters
    ----------
    tag
        The tag to traverse.

    tag_names
        List of tag names to match (e.g., ["mj-text", "mj-button"]).
        If None, applies to the top-level tag.

    attributes
        Attributes to apply to matching tags.

    Returns
    -------
    MJMLTag
        The tag with attributes applied.
    """
    if tag_names is None:
        # Apply to the tag itself
        merged_attrs = {**(tag.attrs or {}), **attributes}
        tag.attrs = merged_attrs
    else:
        # Recursively apply to matching child tags
        def apply_to_children(current_tag: MJMLTag) -> None:
            if current_tag.children:
                for child in current_tag.children:
                    if isinstance(child, MJMLTag):
                        if child.tagName in tag_names:
                            if child.attrs is None:
                                child.attrs = {}
                            child.attrs.update(attributes)
                        apply_to_children(child)

        apply_to_children(tag)

    return tag
