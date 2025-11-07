import json
import pytest
from email.message import EmailMessage
from base64 import b64encode

from nbmail.ingress import (
    redmail_to_intermediate_email,
    yagmail_to_intermediate_email,
    mjml_to_intermediate_email,
    quarto_json_to_intermediate_email,
    _email_message_to_intermediate_email,
)
from nbmail.structs import IntermediateEmail


def test_email_message_to_intermediate_email_simple():
    msg = EmailMessage()
    msg["Subject"] = "Test Subject"
    msg["To"] = "recipient@example.com"
    msg.set_content("Plain text")
    msg.add_alternative("<html><body><p>HTML content</p></body></html>", subtype="html")

    result = _email_message_to_intermediate_email(msg)

    assert result.subject == "Test Subject"
    assert result.recipients == ["recipient@example.com"]
    assert "<p>HTML content</p>" in result.html
    assert result.text == "Plain text\n"
    assert result.inline_attachments is None
    assert result.external_attachments is None


def test_email_message_to_intermediate_email_multiple_recipients():
    msg = EmailMessage()
    msg["Subject"] = "Multi-recipient"
    msg["To"] = "to1@example.com, to2@example.com"
    msg["Cc"] = "cc@example.com"
    msg["Bcc"] = "bcc@example.com"
    msg.add_alternative("<html><body>Test</body></html>", subtype="html")

    result = _email_message_to_intermediate_email(msg)

    assert len(result.recipients) == 4
    assert "to1@example.com" in result.recipients
    assert "to2@example.com" in result.recipients
    assert "cc@example.com" in result.recipients
    assert "bcc@example.com" in result.recipients


def test_email_message_to_intermediate_email_with_inline_image():
    msg = EmailMessage()
    msg["Subject"] = "With Image"
    msg.add_alternative("<html><body><img src='cid:img1'></body></html>", subtype="html")
    
    # Add inline image
    img_data = b"\x89PNG\r\n\x1a\n"
    msg.add_attachment(img_data, maintype="image", subtype="png", cid="img1")

    result = _email_message_to_intermediate_email(msg)

    assert result.inline_attachments is not None
    assert "img1" in result.inline_attachments
    assert result.inline_attachments["img1"] == b64encode(img_data).decode("utf-8")


def test_email_message_to_intermediate_email_with_external_attachment():
    msg = EmailMessage()
    msg["Subject"] = "With Attachment"
    msg.add_alternative("<html><body>Content</body></html>", subtype="html")
    msg.add_attachment(b"file content", maintype="application", subtype="pdf", filename="document.pdf")

    result = _email_message_to_intermediate_email(msg)

    assert result.external_attachments is not None
    assert "document.pdf" in result.external_attachments


def test_email_message_to_intermediate_email_plain_text_only():
    msg = EmailMessage()
    msg["Subject"] = "Plain Only"
    msg.set_content("Just plain text")

    result = _email_message_to_intermediate_email(msg)

    assert result.text == "Just plain text\n"
    assert result.html == ""  # Empty string when no HTML


def test_email_message_to_intermediate_email_html_only_not_multipart():
    msg = EmailMessage()
    msg["Subject"] = "HTML Only"
    msg.set_content("<html><body>HTML</body></html>", subtype="html")

    result = _email_message_to_intermediate_email(msg)

    assert result.html == "<html><body>HTML</body></html>\n"
    assert result.text is None


def test_redmail_to_intermediate_email():
    msg = EmailMessage()
    msg["Subject"] = "Redmail Test"
    msg.add_alternative("<html><body>Redmail content</body></html>", subtype="html")

    result = redmail_to_intermediate_email(msg)

    assert isinstance(result, IntermediateEmail)
    assert result.subject == "Redmail Test"
    assert "Redmail content" in result.html


def test_yagmail_to_intermediate_email_not_implemented():
    result = yagmail_to_intermediate_email()
    assert result is None


def test_mjml_to_intermediate_email_no_images():
    mjml_content = """
    <mjml>
      <mj-body>
        <mj-section>
          <mj-column>
            <mj-text>Hello World</mj-text>
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>
    """

    result = mjml_to_intermediate_email(mjml_content)

    assert isinstance(result, IntermediateEmail)
    assert "Hello World" in result.html
    assert result.subject == ""
    assert result.inline_attachments == {}


def test_mjml_to_intermediate_email_with_string_url():
    mjml_content = """
    <mjml>
      <mj-body>
        <mj-section>
          <mj-column>
            <mj-image src="https://example.com/image.jpg" />
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>
    """

    result = mjml_to_intermediate_email(mjml_content)
    
    assert isinstance(result, IntermediateEmail)
    assert result.inline_attachments == {}
    assert "https://example.com/image.jpg" in result.html


def test_mjml_to_intermediate_email_with_bytesio():
    from io import BytesIO
    from nbmail.mjml import mjml, body, section, column, image
    
    buf = BytesIO(b'\x89PNG\r\n\x1a\n')
    
    mjml_tag = mjml(
        body(
            section(
                column(
                    image(attributes={
                        "src": buf,
                        "alt": "Test Plot",
                        "width": "600px"
                    })
                )
            )
        )
    )
    
    result = mjml_to_intermediate_email(mjml_tag)
    
    assert isinstance(result, IntermediateEmail)
    assert len(result.inline_attachments) == 1

    cid_filename = list(result.inline_attachments.keys())[0]
    assert cid_filename.endswith(".png")
    assert f"cid:{cid_filename}" in result.html
    assert result.inline_attachments[cid_filename] != ""


def test_mjml_to_mjml_with_bytesio_raises_error():
    from io import BytesIO
    from nbmail.mjml import mjml, body, section, column, image
    
    # Create a simple BytesIO object with fake image data
    buf = BytesIO(b'\x89PNG\r\n\x1a\n')
    
    mjml_tag = mjml(
        body(
            section(
                column(
                    image(attributes={
                        "src": buf,
                        "alt": "Test Plot",
                        "width": "600px"
                    })
                )
            )
        )
    )
    
    # Calling _to_mjml() should raise an error with a helpful message
    with pytest.raises(ValueError, match="Cannot render MJML with BytesIO/bytes"):
        mjml_tag._to_mjml()
    
    # But passing the tag directly to mjml_to_intermediate_email should work
    result = mjml_to_intermediate_email(mjml_tag)
    assert isinstance(result, IntermediateEmail)
    assert len(result.inline_attachments) == 1


def test_quarto_json_to_intermediate_email_basic(tmp_path):
    json_data = {
        "rsc_email_body_html": "<html><body><p>Quarto email</p></body></html>",
        "rsc_email_subject": "Quarto Test",
        "rsc_email_body_text": "Plain text version",
        "rsc_output_files": ["output.pdf"],
        "rsc_email_attachments": ["attachment.csv"],
        "rsc_email_images": {"img1": "base64encodedstring"},
        "rsc_email_supress_report_attachment": True,
        "rsc_email_supress_scheduled": False,
    }

    json_file = tmp_path / "metadata.json"
    with open(json_file, "w") as f:
        json.dump(json_data, f)

    result = quarto_json_to_intermediate_email(str(json_file))

    assert result.subject == "Quarto Test"
    assert "<p>Quarto email</p>" in result.html
    assert result.text == "Plain text version"
    assert result.external_attachments == ["output.pdf", "attachment.csv"]
    assert result.inline_attachments == {"img1": "base64encodedstring"}
    assert result.rsc_email_supress_report_attachment is True
    assert result.rsc_email_supress_scheduled is False


def test_quarto_json_to_intermediate_email_minimal(tmp_path):
    json_data = {
        "rsc_email_body_html": "<html><body>Minimal</body></html>",
        "rsc_email_subject": "Minimal Subject",
    }

    json_file = tmp_path / "minimal.json"
    with open(json_file, "w") as f:
        json.dump(json_data, f)

    result = quarto_json_to_intermediate_email(str(json_file))

    assert result.subject == "Minimal Subject"
    assert result.html == "<html><body>Minimal</body></html>"
    assert result.text == ""
    assert result.external_attachments == []
    assert result.inline_attachments == {}
    assert result.rsc_email_supress_report_attachment is False
    assert result.rsc_email_supress_scheduled is False


def test_quarto_json_to_intermediate_email_empty_lists(tmp_path):
    """Test handling empty lists for attachments and images."""
    json_data = {
        "rsc_email_body_html": "<html><body>Test</body></html>",
        "rsc_email_subject": "Empty Lists",
        "rsc_output_files": [],
        "rsc_email_attachments": [],
        "rsc_email_images": {},
    }

    json_file = tmp_path / "empty.json"
    with open(json_file, "w") as f:
        json.dump(json_data, f)

    result = quarto_json_to_intermediate_email(str(json_file))

    assert result.external_attachments == []
    assert result.inline_attachments == {}
