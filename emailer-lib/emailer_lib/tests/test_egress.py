from unittest.mock import patch, MagicMock, mock_open


import pytest
from emailer_lib.egress import (
    send_intermediate_email_with_redmail,
    send_intermediate_email_with_yagmail,
    send_intermediate_email_with_mailgun,
    send_intermediate_email_with_smtp,
    send_intermediate_email_with_gmail,
    send_quarto_email_with_gmail,
)
from emailer_lib.structs import IntermediateEmail


def make_basic_email():
    return IntermediateEmail(
        html="<p>Hi</p>",
        subject="Test",
        recipients=["a@example.com"],
        text="Plain text",
        inline_attachments={"img.png": "iVBORw0KGgoAAAANSUhEUgAAAAUA"},
        external_attachments=[],
    )


def setup_smtp_mocks(monkeypatch):
    mock_server = MagicMock()
    mock_smtp = MagicMock(return_value=mock_server)
    mock_smtp_ssl = MagicMock(return_value=mock_server)

    context = mock_smtp.return_value.__enter__.return_value

    # Patch in the emailer_lib.egress module where they're used
    monkeypatch.setattr("emailer_lib.egress.smtplib.SMTP", mock_smtp)
    monkeypatch.setattr("emailer_lib.egress.smtplib.SMTP_SSL", mock_smtp_ssl)

    return mock_smtp, mock_smtp_ssl, context


def test_send_intermediate_email_with_gmail_calls_smtp(monkeypatch):
    email = make_basic_email()

    mock_smtp_send = MagicMock()
    monkeypatch.setattr(
        "emailer_lib.egress.send_intermediate_email_with_smtp", mock_smtp_send
    )

    send_intermediate_email_with_gmail("user@gmail.com", "pass", email)

    mock_smtp_send.assert_called_once_with(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username="user@gmail.com",
        password="pass",
        i_email=email,
        use_tls=True,
    )


def test_send_intermediate_email_with_smtp_tls(monkeypatch):
    email = make_basic_email()
    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    send_intermediate_email_with_smtp(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="user",
        password="pass",
        i_email=email,
        use_tls=True,
    )

    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    context.starttls.assert_called_once()
    context.login.assert_called_once_with("user", "pass")
    context.sendmail.assert_called_once()


def test_send_intermediate_email_with_smtp_ssl(monkeypatch):
    email = make_basic_email()
    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    send_intermediate_email_with_smtp(
        smtp_host="smtp.example.com",
        smtp_port=465,
        username="user",
        password="pass",
        i_email=email,
        use_tls=False,
    )

    mock_smtp_ssl.assert_called_once_with("smtp.example.com", 465)
    context.login.assert_called_once_with("user", "pass")
    context.sendmail.assert_called_once()


def test_send_intermediate_email_with_smtp_with_attachment(monkeypatch):
    email = make_basic_email()
    email.external_attachments = ["file.txt"]

    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    with patch("builtins.open", mock_open(read_data=b"data")):
        send_intermediate_email_with_smtp(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            i_email=email,
            use_tls=True,
        )

    context.sendmail.assert_called_once()
    args, kwargs = context.sendmail.call_args
    email_message = args[2]
    assert 'Content-Disposition: attachment; filename="file.txt"' in email_message


def test_send_intermediate_email_with_smtp_unknown_mime_type(monkeypatch):
    email = make_basic_email()
    email.external_attachments = ["file_without_extension"]

    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    with patch("builtins.open", mock_open(read_data=b"data")):
        send_intermediate_email_with_smtp(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            i_email=email,
            use_tls=True,
        )

    context.sendmail.assert_called_once()
    args, kwargs = context.sendmail.call_args
    email_message = args[2]

    assert "Content-Type: application/octet-stream" in email_message
    assert (
        'Content-Disposition: attachment; filename="file_without_extension"'
        in email_message
    )


def test_send_intermediate_email_with_smtp_sendmail_args(monkeypatch):
    """Test that sendmail is called with correct sender, recipients, and message format."""
    email = make_basic_email()
    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    send_intermediate_email_with_smtp(
        smtp_host="mock_host",
        smtp_port=465,
        username="user@gmail.com",
        password="pass",
        i_email=email,
        use_tls=False,  # Port 465 uses SSL
    )

    context.sendmail.assert_called_once()

    # Extract sendmail arguments
    args, kwargs = context.sendmail.call_args
    sender = args[0]
    recipients = args[1]
    raw_message = args[2]

    assert sender == "user@gmail.com"
    assert recipients == ["a@example.com"]

    assert "Subject: Test" in raw_message
    assert "text/html" in raw_message or "<p>Hi</p>" in raw_message


# this is probably not the best way to test this,
# for what it's worth I will test each part separately
def test_send_quarto_email_with_gmail(monkeypatch):
    # Mock the quarto_json_to_intermediate_email function
    mock_quarto_to_email = MagicMock(return_value=make_basic_email())
    monkeypatch.setattr(
        "emailer_lib.egress.quarto_json_to_intermediate_email", mock_quarto_to_email
    )

    # Mock the Gmail sending function
    mock_send_gmail = MagicMock()
    monkeypatch.setattr(
        "emailer_lib.egress.send_intermediate_email_with_gmail", mock_send_gmail
    )

    # Call the function
    send_quarto_email_with_gmail(
        username="user@gmail.com",
        password="pass",
        json_path="path/to/metadata.json",
        recipients=["recipient@example.com"],
    )

    mock_quarto_to_email.assert_called_once_with("path/to/metadata.json")
    mock_send_gmail.assert_called_once()

    _, kwargs = mock_send_gmail.call_args
    i_email = kwargs.get("i_email")
    assert i_email.recipients == ["recipient@example.com"]


@pytest.mark.parametrize(
    "send_func",
    [
        send_intermediate_email_with_redmail,
        send_intermediate_email_with_yagmail,
        send_intermediate_email_with_mailgun,
    ],
)
def test_not_implemented_functions(send_func):
    """Test that unimplemented send functions raise NotImplementedError."""
    email = make_basic_email()
    with pytest.raises(NotImplementedError):
        send_func(email)
