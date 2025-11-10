import pytest

from nbmail.compose import (
    compose_email,
    block_text,
    block_title,
    block_spacer,
    create_blocks,
)
from nbmail.structs import Email


def test_block_text_simple():
    block = block_text("Hello world")
    email = compose_email(body=block)

    assert "Hello world" in email.html


@pytest.mark.parametrize("align", ["left", "center", "right", "justify"])
def test_block_text_with_alignment(align):
    block = block_text("Test block", align=align)
    email = compose_email(body=block)

    assert "Test block" in email.html
    assert f"text-align:{align}" in email.html


def test_block_text_with_markdown():
    block = block_text("This is **bold** and *italic*")
    email = compose_email(body=block)

    assert "<strong>bold</strong>" in email.html
    assert "<em>italic</em>" in email.html


def test_block_title_simple():
    block = block_title("My Title")
    email = compose_email(body=block)

    assert "My Title" in email.html
    assert "text-align:center;color:#000000;" in email.html
    # assert False


def test_block_title_with_markdown():
    block = block_title("**Important** Title")
    email = compose_email(body=block)

    assert "<strong>Important</strong>" in email.html
    assert "Title" in email.html


def test_block_spacer_default():
    email = compose_email(
        body=create_blocks(
            block_text("Before"),
            block_spacer(),
            block_text("After"),
        )
    )

    assert "Before" in email.html
    assert '<div style="height:20px;line-height:20px;">' in email.html
    assert "After" in email.html


def test_block_spacer_custom_height():
    for height in ["50px", "2em"]:
        email = compose_email(
            body=create_blocks(
                block_text("Before"),
                block_spacer(height),
                block_text("After"),
            )
        )

        assert "Before" in email.html
        assert f'<div style="height:{height};' in email.html
        assert "After" in email.html


def test_create_blocks_with_multiple_blocks():
    block_list = create_blocks(
        block_title("Title"),
        block_text("Content"),
        block_spacer("20px"),
    )

    assert block_list is not None
    assert len(block_list.items) == 3


def test_create_blocks_with_strings():
    block_list = create_blocks("Hello", "World")

    assert block_list is not None
    assert len(block_list.items) == 2


def test_create_blocks_mixed_content():
    block_list = create_blocks(
        block_text("First"),
        "Second string",
        block_title("Third"),
    )

    assert block_list is not None
    assert len(block_list.items) == 3


def test_compose_email_with_body_string():
    email = compose_email(body="Hello world")

    assert isinstance(email, Email)
    assert "Hello world" in email.html


def test_compose_email_with_sections():
    email = compose_email(
        header=block_text("Header content"),
        body=block_text("Body content"),
        footer=block_text("Footer content"),
    )

    assert "Header content" in email.html
    assert "Body content" in email.html
    assert "Footer content" in email.html


def test_compose_email_with_title():
    email = compose_email(
        title="My Subject",
        body=block_text("Content"),
    )

    assert email.subject == ""
    assert "My Subject" in email.html
    assert "Content" in email.html


def test_compose_email_empty():
    email = compose_email()

    assert isinstance(email, Email)
    assert email.html is not None


def test_compose_email_all_sections():
    email = compose_email(
        header=create_blocks(block_title("Newsletter")),
        body=create_blocks(
            block_text("Welcome!"),
            block_spacer("20px"),
            block_text("Content here..."),
        ),
        footer=create_blocks(
            block_text("© 2025 Company"),
        ),
        title="Weekly Update",
    )

    assert "Newsletter" in email.html
    assert "Welcome!" in email.html
    assert '<div style="height:20px;line-height:20px;">' in email.html
    assert "Content here..." in email.html
    assert "© 2025 Company" in email.html
    assert "Weekly Update" in email.html


def test_compose_email_invalid_template():
    try:
        compose_email(
            body=block_text("Content"),
            template="invalid_template",
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown template" in str(e)
        assert "blastula" in str(e) or "none" in str(e)


def test_blocks_preserve_order_in_html():
    email = compose_email(
        body=create_blocks(
            block_title("Report"),
            block_spacer("20px"),
            block_text("Here's the data:"),
            block_spacer("10px"),
            block_text("- Item 1\n- Item 2"),
        )
    )

    # Check relative positioning
    html = email.html
    report_idx = html.index("Report")
    data_idx = html.index("Here's the data:")
    item1_idx = html.index("Item 1")

    assert report_idx < data_idx < item1_idx, (
        "Blocks should appear in order: Report → Data → Items"
    )


def test_blocklist_repr():
    block_list = create_blocks(
        block_text("First"),
        block_text("Second"),
        block_text("Third"),
    )

    repr_str = repr(block_list)
    assert "<BlockList: 3 items>" in repr_str
