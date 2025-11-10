"""Tests for compose module utility functions."""

from datetime import datetime

import pytest

from nbmail.compose import (
    md,
    add_image,
    add_cta_button,
    add_readable_time,
)


def test_md_simple_text():
    result = md("Hello world")

    assert result == "<p>Hello world</p>"


def test_md_bold():
    result = md("**bold**")
    assert "<p><strong>bold</strong></p>" == result


def test_md_italic():
    result = md("*italic*")
    assert "<p><em>italic</em></p>" == result


def test_md_list():
    result = md("- Item 1\n- Item 2")

    assert "<li>Item 1</li>" in result
    assert "<li>Item 2</li>" in result


def test_md_heading():
    result = md("# Heading 1")

    assert "Heading 1</h1>" in result


def test_add_image_url():
    html = add_image("https://example.com/image.png", alt="Test image")

    assert "<img" in html
    assert 'src="https://example.com/image.png"' in html
    assert 'alt="Test image"' in html


def test_add_image_default_width():
    html = add_image("test.png")

    assert 'width="520px"' in html


def test_add_image_custom_width():
    html = add_image("test.png", width="600px")

    assert 'width="600px"' in html


def test_add_image_alignment():
    html = add_image("test.png", align="center")
    assert "display: block; margin: 0 auto;" in html

    html = add_image("test.png", align="left")
    assert "display: block; margin: 0;" in html

    html = add_image("test.png", align="right")
    assert "float: right;" in html


def test_add_cta_button_basic():
    html = add_cta_button("Click Me", "https://example.com")

    assert "<a" in html
    assert 'href="https://example.com"' in html
    assert ">Click Me</a>" in html


def test_add_cta_button_colors():
    html = add_cta_button(
        "Button", "https://example.com", bg_color="#FF0000", text_color="#FFFFFF"
    )

    assert "#FF0000" in html
    assert "#FFFFFF" in html

@pytest.mark.xfail
def test_add_readable_time_default_format():
    dt = datetime(2025, 11, 10)
    result = add_readable_time(dt)

    assert "November" in result
    assert "2025" in result


@pytest.mark.xfail
def test_add_readable_time_custom_format():
    dt = datetime(2025, 11, 10, 14, 30, 0)
    result = add_readable_time(dt, format_str="%Y-%m-%d")
    assert result == "2025-11-10"
