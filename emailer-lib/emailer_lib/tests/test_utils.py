import base64
from email.message import EmailMessage
import re

from emailer_lib.utils import (
    write_email_message_to_file,
    _add_base_64_to_inline_attachments,
)


def test_write_email_message_to_file_basic(tmp_path):
    """Test writing a simple HTML email to a file."""
    msg = EmailMessage()
    msg.set_content("Plain text", subtype="plain")
    msg.add_alternative("<html><body><p>Hello World</p></body></html>", subtype="html")

    out_file = tmp_path / "output.html"
    write_email_message_to_file(msg, str(out_file))

    content = out_file.read_text(encoding="utf-8")
    assert "<p>Hello World</p>" in content
    assert "cid:" not in content
    assert "data:" not in content


def test_write_email_message_to_file_with_inline_image(tmp_path):
    msg = EmailMessage()

    html = '<html><body><p>Image:</p><img src="cid:image1"></body></html>'
    msg.add_alternative(html, subtype="html")

    # Add an inline image
    img_data = b"\x89PNG\r\n\x1a\n"  # Fake PNG header
    msg.add_attachment(img_data, maintype="image", subtype="png", cid="image1")

    out_file = tmp_path / "output_with_image.html"
    write_email_message_to_file(msg, str(out_file))

    content = out_file.read_text(encoding="utf-8")

    assert 'src="cid:image1"' not in content
    assert 'src="data:image;base64,' in content
    assert base64.b64encode(img_data).decode("utf-8") in content


def test_write_email_message_to_file_multiple_inline_images(tmp_path):
    msg = EmailMessage()

    html = """<html><body>
        <img src="cid:img1">
        <img src="cid:img2">
    </body></html>"""
    msg.add_alternative(html, subtype="html")

    # Add two inline images
    for i, cid in enumerate(["img1", "img2"]):
        img_data = bytes([i + 1])  # Different data for each
        msg.add_attachment(img_data, maintype="image", subtype="png", cid=cid)

    out_file = tmp_path / "output_multi.html"
    write_email_message_to_file(msg, str(out_file))

    content = out_file.read_text(encoding="utf-8")
    assert 'src="cid:img1"' not in content
    assert 'src="cid:img2"' not in content
    assert content.count('src="data:image;base64,') == 2


def test_write_email_message_to_file_default_filename(tmp_path, monkeypatch):
    msg = EmailMessage()
    msg.add_alternative("<html><body><p>Default</p></body></html>", subtype="html")

    # Change to tmp directory
    monkeypatch.chdir(tmp_path)

    write_email_message_to_file(msg)

    # Check default file was created
    default_file = tmp_path / "preview_email.html"
    assert default_file.exists()

    content = default_file.read_text(encoding="utf-8")
    assert "<p>Default</p>" in content


def test_add_base_64_to_inline_attachments_single_image():
    inline_attachments = {"img1": b"\x89PNG\r\n\x1a\n"}

    html = '<html><body><img src="cid:img1"></body></html>'
    result = re.sub(
        r'src="cid:([^"\s]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    assert 'src="cid:img1"' not in result
    assert 'src="data:image;base64,' in result

    expected_base64 = base64.b64encode(inline_attachments["img1"]).decode("utf-8")
    assert expected_base64 in result


def test_add_base_64_to_inline_attachments_multiple_images():
    inline_attachments = {"img1": b"image1data", "img2": b"image2data"}

    html = """<html><body>
        <img src="cid:img1">
        <img src="cid:img2">
    </body></html>"""

    result = re.sub(
        r'src="cid:([^"\s]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    assert 'src="cid:img1"' not in result
    assert 'src="cid:img2"' not in result
    assert result.count('src="data:image;base64,') == 2

    expected_base64_1 = base64.b64encode(inline_attachments["img1"]).decode("utf-8")
    expected_base64_2 = base64.b64encode(inline_attachments["img2"]).decode("utf-8")
    assert expected_base64_1 in result
    assert expected_base64_2 in result


def test_add_base_64_to_inline_attachments_missing_cid():
    inline_attachments = {"img1": b"image1data"}

    html = '<html><body><img src="cid:missing"></body></html>'
    result = re.sub(
        r'src="cid:([^"\s]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    # Missing cid should remain unchanged
    assert 'src="cid:missing"' in result


def test_add_base_64_to_inline_attachments_empty_dict():
    inline_attachments = {}

    html = '<html><body><img src="cid:img1"></body></html>'
    result = re.sub(
        r'src="cid:([^"\s]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    # Should remain unchanged
    assert 'src="cid:img1"' in result


def test_add_base_64_to_inline_attachments_no_cid_in_html():
    inline_attachments = {"img1": b"image1data"}

    html = '<html><body><img src="https://example.com/image.png"></body></html>'
    result = re.sub(
        r'src="cid:([^"\s]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    # Should remain unchanged
    assert html == result


def test_add_base_64_to_inline_attachments_string_base64():
    img_bytes = b"image_data_here"
    base64_string = base64.b64encode(img_bytes).decode("utf-8")

    inline_attachments = {
        "img1": base64_string  # String, not bytes
    }

    html = '<html><body><img src="cid:img1"></body></html>'
    result = re.sub(
        r'src="cid:([^"\s]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    assert 'src="cid:img1"' not in result
    assert 'src="data:image;base64,' in result
    assert base64_string in result


def test_add_base_64_to_inline_attachments_string_not_base64():
    non_base64_string = "not_valid_base64!@#$"

    inline_attachments = {
        "img1": non_base64_string  # String that's not valid base64
    }

    html = '<html><body><img src="cid:img1"></body></html>'
    result = re.sub(
        r'src="cid:([^"\s]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    assert 'src="cid:img1"' not in result
    assert 'src="data:image;base64,' in result

    # Should encode the string as UTF-8 bytes, then base64 encode
    expected_base64 = base64.b64encode(non_base64_string.encode("utf-8")).decode(
        "utf-8"
    )
    assert expected_base64 in result
