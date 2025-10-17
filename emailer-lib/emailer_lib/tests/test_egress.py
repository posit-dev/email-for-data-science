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


def test_send_intermediate_email_with_gmail_mocks_smtp(monkeypatch):
    email = make_basic_email()
    mock_server = MagicMock()

    # This ensures the smtplib.SMTP_SSL call in send_intermediate_email_with_gmail
    # uses our mock server
    mock_smtp_ssl = MagicMock(return_value=mock_server)

    # This retrieves the mock object that will be used as 'server' inside
    # the 'with ... as server:' block
    context = mock_smtp_ssl.return_value.__enter__.return_value
    monkeypatch.setattr("smtplib.SMTP_SSL", mock_smtp_ssl)

    send_intermediate_email_with_gmail("user", "pass", email)
    context.login.assert_called_once_with("user", "pass")
    context.sendmail.assert_called_once()

    args, kwargs = context.sendmail.call_args
    email_message = args[2]  # The raw email message as a string
    assert "Content-ID: <img.png>" in email_message


def test_send_intermediate_email_with_gmail_with_attachment(monkeypatch):
    email = make_basic_email()

    # Add a fake external attachment
    email.external_attachments = ["file.txt"]
    mock_server = MagicMock()
    mock_smtp_ssl = MagicMock(return_value=mock_server)

    context = mock_smtp_ssl.return_value.__enter__.return_value
    monkeypatch.setattr("smtplib.SMTP_SSL", mock_smtp_ssl)

    # This mocks the built-in open function so that when the functoin opens "file.txt"
    # to read its contents (for attaching to the email), it gets the fake data (b"data")
    # instead of actually reading a file from disk
    with patch("builtins.open", mock_open(read_data=b"data")):
        send_intermediate_email_with_gmail("user", "pass", email)
    context.login.assert_called_once_with("user", "pass")
    context.sendmail.assert_called_once()

    args, kwargs = context.sendmail.call_args
    email_message = args[2]
    assert 'Content-Disposition: attachment; filename="file.txt"' in email_message

def test_send_intermediate_email_with_gmail_unknown_mime_type(monkeypatch):
    email = make_basic_email()
    
    # Add an attachment with no extension (unknown MIME type)
    email.external_attachments = ["file_without_extension"]
    mock_server = MagicMock()
    mock_smtp_ssl = MagicMock(return_value=mock_server)
    context = mock_smtp_ssl.return_value.__enter__.return_value
    monkeypatch.setattr("smtplib.SMTP_SSL", mock_smtp_ssl)
    
    with patch("builtins.open", mock_open(read_data=b"data")):
        send_intermediate_email_with_gmail("user", "pass", email)
    
    context.sendmail.assert_called_once()
    
    args, kwargs = context.sendmail.call_args
    email_message = args[2]
    
    assert "Content-Type: application/octet-stream" in email_message
    assert 'Content-Disposition: attachment; filename="file_without_extension"' in email_message

def test_send_intermediate_email_with_gmail_uses_correct_server(monkeypatch):
    email = make_basic_email()
    mock_server = MagicMock()
    mock_smtp_ssl = MagicMock(return_value=mock_server)
    context = mock_smtp_ssl.return_value.__enter__.return_value
    monkeypatch.setattr("smtplib.SMTP_SSL", mock_smtp_ssl)

    send_intermediate_email_with_gmail("user@gmail.com", "pass", email)

    # Verify SMTP_SSL was called with Gmail's server and port
    mock_smtp_ssl.assert_called_once_with("smtp.gmail.com", 465)
    context.login.assert_called_once_with("user@gmail.com", "pass")


def test_send_intermediate_email_with_gmail_sendmail_args(monkeypatch):
    """Test that sendmail is called with correct sender, recipients, and message format."""
    email = make_basic_email()
    mock_server = MagicMock()
    mock_smtp_ssl = MagicMock(return_value=mock_server)
    context = mock_smtp_ssl.return_value.__enter__.return_value
    monkeypatch.setattr("smtplib.SMTP_SSL", mock_smtp_ssl)

    send_intermediate_email_with_gmail("user@gmail.com", "pass", email)

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
        send_intermediate_email_with_smtp,
    ],
)
def test_not_implemented_functions(send_func):
    """Test that unimplemented send functions raise NotImplementedError."""
    email = make_basic_email()
    with pytest.raises(NotImplementedError):
        send_func(email)
