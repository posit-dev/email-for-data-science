from unittest.mock import patch, MagicMock, mock_open


import pytest
from nbmail.egress import (
    send_email_with_redmail,
    send_email_with_yagmail,
    send_email_with_mailgun,
    send_email_with_smtp,
    send_email_with_gmail,
    send_quarto_email_with_gmail,
)
from nbmail.structs import Email


def make_basic_email():
    return Email(
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

    # Patch in the nbmail.egress module where they're used
    monkeypatch.setattr("nbmail.egress.smtplib.SMTP", mock_smtp)
    monkeypatch.setattr("nbmail.egress.smtplib.SMTP_SSL", mock_smtp_ssl)

    return mock_smtp, mock_smtp_ssl, context


def test_send_email_with_gmail_calls_smtp(monkeypatch):
    email = make_basic_email()

    mock_smtp_send = MagicMock()
    monkeypatch.setattr(
        "nbmail.egress.send_email_with_smtp", mock_smtp_send
    )

    send_email_with_gmail("user@gmail.com", "pass", email)

    mock_smtp_send.assert_called_once_with(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username="user@gmail.com",
        password="pass",
        i_email=email,
        security="tls",
    )


def test_send_email_with_smtp_tls(monkeypatch):
    email = make_basic_email()
    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    send_email_with_smtp(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="user",
        password="pass",
        i_email=email,
        security="tls",
    )

    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    context.starttls.assert_called_once()
    context.login.assert_called_once_with("user", "pass")
    context.sendmail.assert_called_once()


def test_send_email_with_smtp_ssl(monkeypatch):
    email = make_basic_email()
    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    send_email_with_smtp(
        smtp_host="smtp.example.com",
        smtp_port=465,
        username="user",
        password="pass",
        i_email=email,
        security="ssl",
    )

    mock_smtp_ssl.assert_called_once_with("smtp.example.com", 465)
    context.login.assert_called_once_with("user", "pass")
    context.sendmail.assert_called_once()


def test_send_email_with_smtp_with_attachment(monkeypatch):
    email = make_basic_email()
    email.external_attachments = ["file.txt"]

    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    with patch("builtins.open", mock_open(read_data=b"data")):
        send_email_with_smtp(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            i_email=email,
            security="tls"
        )

    context.sendmail.assert_called_once()
    args, kwargs = context.sendmail.call_args
    email_message = args[2]
    assert 'Content-Disposition: attachment; filename="file.txt"' in email_message


def test_send_email_with_smtp_unknown_mime_type(monkeypatch):
    email = make_basic_email()
    email.external_attachments = ["file_without_extension"]

    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    with patch("builtins.open", mock_open(read_data=b"data")):
        send_email_with_smtp(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            i_email=email,
            security="tls",
        )

    context.sendmail.assert_called_once()
    args, kwargs = context.sendmail.call_args
    email_message = args[2]

    assert "Content-Type: application/octet-stream" in email_message
    assert (
        'Content-Disposition: attachment; filename="file_without_extension"'
        in email_message
    )


def test_send_email_with_smtp_sendmail_args(monkeypatch):
    email = make_basic_email()
    mock_smtp, mock_smtp_ssl, context = setup_smtp_mocks(monkeypatch)

    send_email_with_smtp(
        smtp_host="mock_host",
        smtp_port=465,
        username="user@gmail.com",
        password="pass",
        i_email=email,
        security="ssl",  # Port 465 uses SSL
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
    # Mock the quarto_json_to_email function
    mock_quarto_to_email = MagicMock(return_value=make_basic_email())
    monkeypatch.setattr(
        "nbmail.egress.quarto_json_to_email", mock_quarto_to_email
    )

    # Mock the Gmail sending function
    mock_send_gmail = MagicMock()
    monkeypatch.setattr(
        "nbmail.egress.send_email_with_gmail", mock_send_gmail
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


def test_send_email_with_mailgun(monkeypatch):
    email = make_basic_email()
    email.external_attachments = ["file.txt"]
    
    # Mock the response object with .json() method
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "<20251028141836.beb7f6b3fd2be2b7@sandboxedc0eedbb2da49f39cbc02665f66556c.mailgun.org>",
        "message": "Queued. Thank you."
    }
    mock_response.__repr__ = lambda self: "<Response [200]>"
    
    # Mock the Mailgun Client
    mock_client_instance = MagicMock()
    mock_messages = MagicMock()
    mock_client_instance.messages = mock_messages
    mock_messages.create = MagicMock(return_value=mock_response)
    
    mock_client_class = MagicMock(return_value=mock_client_instance)
    
    with patch("mailgun.client.Client", mock_client_class):
        with patch("builtins.open", mock_open(read_data=b"file content")):
            response = send_email_with_mailgun(
                api_key="test-api-key",
                domain="mg.example.com",
                sender="sender@example.com",
                i_email=email,
            )
    
    # Verify Client was initialized with correct auth
    mock_client_class.assert_called_once_with(auth=("api", "test-api-key"))
    
    mock_messages.create.assert_called_once()
    call_args = mock_messages.create.call_args
    
    data = call_args.kwargs["data"]
    assert data["from"] == "sender@example.com"
    assert data["to"] == ["a@example.com"]
    assert data["subject"] == "Test"
    assert data["html"] == "<p>Hi</p>"
    assert data["text"] == "Plain text"
    
    # Check files were passed
    files = call_args.kwargs["files"]
    assert files is not None
    assert len(files) == 2  # 1 inline, 1 external
    
    assert call_args.kwargs["domain"] == "mg.example.com"
    
    assert response == mock_response
    assert response.json() == {
        "id": "<20251028141836.beb7f6b3fd2be2b7@sandboxedc0eedbb2da49f39cbc02665f66556c.mailgun.org>",
        "message": "Queued. Thank you."
    }


def test_send_email_with_mailgun_no_recipients():
    email = Email(
        html="<p>Hi</p>",
        subject="Test",
        recipients=None,
    )
    
    with pytest.raises(TypeError, match="i_email must have a populated recipients attribute"):
        send_email_with_mailgun(
            api_key="test-api-key",
            domain="mg.example.com",
            sender="sender@example.com",
            i_email=email,
        )


@pytest.mark.parametrize(
    "send_func",
    [
        send_email_with_redmail,
        send_email_with_yagmail,
    ],
)
def test_not_implemented_functions(send_func):
    email = make_basic_email()
    with pytest.raises(NotImplementedError):
        send_func(email)
