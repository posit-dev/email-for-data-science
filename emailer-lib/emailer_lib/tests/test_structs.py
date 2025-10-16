import re
from emailer_lib.structs import IntermediateEmail


def test_creation_with_text_and_attachments():
    email = IntermediateEmail(
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
    email = IntermediateEmail(
        html="<p>Hi</p>",
        subject="No Text or Attachments",
    )
    assert email.text is None
    assert email.recipients is None
    assert email.external_attachments is None
    assert email.inline_attachments is None
    assert email.subject == "No Text or Attachments"


def test_subject_inserts_after_body(tmp_path):
    html = "<html><body><p>Hello!</p></body></html>"
    email = IntermediateEmail(
        html=html,
        subject="Test Subject",
        rsc_email_supress_report_attachment=False,
        rsc_email_supress_scheduled=False,
    )
    out_file = tmp_path / "preview.html"

    email.write_preview_email(str(out_file))
    content = out_file.read_text(encoding="utf-8")

    # Check subject is inserted after <body>
    assert re.search(
        r"<body[^>]*>\s*<h2 style=\"padding-left:16px;\">Subject: Test Subject</h2>",
        content,
        re.IGNORECASE,
    )


def test_subject_prepends_if_no_body(tmp_path):
    html = "<p>Hello!</p>"
    email = IntermediateEmail(
        html=html,
        subject="NoBody",
    )
    out_file = tmp_path / "preview2.html"
    email.write_preview_email(str(out_file))
    content = out_file.read_text(encoding="utf-8")
    # Should start with the subject h2
    assert content.startswith('<h2 style="padding-left:16px;">Subject: NoBody</h2>')


def test_raises_on_external_attachments(tmp_path):
    html = "<p>Test</p>"
    email = IntermediateEmail(
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
