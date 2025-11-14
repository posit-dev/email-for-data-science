import re

import pytest
from nbmail.structs import Email


def test_creation_with_text_and_attachments():
    email = Email(
        html="<p>Hi</p>",
        subject="With Text and Attachments",
        text="Plain text version",
        recipients=["a@example.com"],
        external_attachments=["/tmp/file1.txt"],
        inline_attachments={"img.png": "base64string"},
    )
    assert email.text == "Plain text version"
    assert email.recipients == ["a@example.com"]
    assert email.external_attachments == ["/tmp/file1.txt"]
    assert email.inline_attachments == {"img.png": "base64string"}
    assert email.subject == "With Text and Attachments"


def test_creation_without_text_and_attachments():
    email = Email(
        html="<p>Hi</p>",
        subject="No Text or Attachments",
    )
    assert email.text is None
    assert email.recipients is None
    assert email.external_attachments == []
    assert email.inline_attachments == {}
    assert email.subject == "No Text or Attachments"


def test_subject_inserts_after_body(tmp_path):
    html = "<html><body><p>Hello!</p></body></html>"
    email = Email(
        html=html,
        subject="Test Subject",
        email_suppress_report_attachment=False,
        email_suppress_scheduled=False,
    )
    out_file = tmp_path / "preview.html"

    email.write_preview_email(str(out_file))
    content = out_file.read_text(encoding="utf-8")

    assert re.search(
        r'<html><body><br><br><strong><span style="font-variant: small-caps;">email subject:',
        content,
    )


def test_subject_prepends_if_no_body(tmp_path):
    html = "<p>Hello!</p>"
    email = Email(
        html=html,
        subject="NoBody",
    )
    out_file = tmp_path / "preview2.html"
    email.write_preview_email(str(out_file))
    content = out_file.read_text(encoding="utf-8")

    assert content == '<br><br><strong><span style="font-variant: small-caps;">email subject: </span></strong>NoBody<br><p>Hello!</p>'


def test_raises_on_external_attachments(tmp_path):
    html = "<p>Test</p>"
    email = Email(
        html=html,
        subject="Test",
        external_attachments=["file.txt"],
    )
    out_file = tmp_path / "preview3.html"
    try:
        email.write_preview_email(str(out_file))
    except ValueError as e:
        assert "external attachments" in str(e)
    else:
        assert False, "Expected ValueError for external attachments"


@pytest.mark.parametrize(
    "method_name",
    ["write_email_message", "preview_send_email"],
)
def test_not_implemented_methods(method_name):
    """Test that unimplemented methods raise NotImplementedError."""
    email = Email(
        html="<p>Hi</p>",
        subject="Test",
    )
    method = getattr(email, method_name)
    with pytest.raises(NotImplementedError):
        method()


def test_preview_email_simple_html(tmp_path, snapshot):
    html = "<html><body><p>Hello World!</p></body></html>"
    email = Email(
        html=html,
        subject="Simple Test Email",
    )
    
    out_file = tmp_path / "preview.html"
    email.write_preview_email(str(out_file))
    content = out_file.read_text(encoding="utf-8")
    
    assert content == snapshot


def test_preview_email_with_inline_attachments(tmp_path, snapshot):
    html = """<html>
<body>
<h1>Email with Images</h1>
<img src="cid:logo.png" alt="Logo" />
<p>Some text content</p>
<img src="cid:banner.jpg" alt="Banner" />
</body>
</html>"""
    email = Email(
        html=html,
        subject="Email with Inline Images",
        inline_attachments={
            "logo.png": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "banner.jpg": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAAA="
        },
    )

    out_file = tmp_path / "preview.html"
    email.write_preview_email(str(out_file))
    content = out_file.read_text(encoding="utf-8")
    
    assert content == snapshot


def test_preview_email_complex_html(tmp_path, snapshot):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Email</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { background-color: #f0f0f0; padding: 20px; }
        .content { padding: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome!</h1>
    </div>
    <div class="content">
        <p>This is a <strong>complex</strong> email with <em>formatting</em>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
        <img src="cid:test.png" alt="Test Image" />
    </div>
</body>
</html>"""
    email = Email(
        html=html,
        subject="Complex Email Structure",
        inline_attachments={
            "test.png": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        },
    )
    
    out_file = tmp_path / "preview.html"
    email.write_preview_email(str(out_file))
    content = out_file.read_text(encoding="utf-8")
    
    assert content == snapshot
