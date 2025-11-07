import pytest
import time
from aiosmtpd.controller import Controller
from email import message_from_bytes
from nbmail.egress import send_email_with_smtp
from nbmail.structs import Email


class EmailHandler:
    def __init__(self):
        self.messages = []
    
    async def handle_DATA(self, server, session, envelope):
        self.messages.append({
            'peer': session.peer,
            'mail_from': envelope.mail_from,
            'rcpt_tos': envelope.rcpt_tos,
            'data': envelope.content,
        })
        return '250 Message accepted for delivery'


@pytest.fixture
def smtp_server():
    handler = EmailHandler()
    controller = Controller(handler, hostname='127.0.0.1', port=8025)
    controller.start()
    
    # Wait for server to be ready
    # time.sleep(0.1)
    
    yield controller, handler
    
    controller.stop()


def test_send_email_integration(smtp_server):
    controller, handler = smtp_server
    
    email = Email(
        html="<html><body><h1>Test Email</h1><p>Hello World</p></body></html>",
        subject="Integration Test",
        recipients=["test@example.com"],
        text="Plain text version",
        inline_attachments={"img.png": "iVBORw0KGgoAAAANSUhEUgAAAAUA"},
        external_attachments=[],
    )
    
    # Send email to the test SMTP server
    send_email_with_smtp(
        smtp_host="127.0.0.1",
        smtp_port=8025,
        username="test@example.com",
        password="password",
        i_email=email,
        security="smtp",
    )
    
    # Wait for message to be processed
    time.sleep(0.1)
    
    # Verify the email was received
    assert len(handler.messages) == 1, f"Expected 1 message, got {len(handler.messages)}"
    
    msg_data = handler.messages[0]['data']
    msg = message_from_bytes(msg_data)
    
    # Test email headers
    assert msg['Subject'] == "Integration Test"
    assert msg['To'] == "test@example.com"
    assert handler.messages[0]['mail_from'] == "test@example.com"
    assert "test@example.com" in handler.messages[0]['rcpt_tos']
    
    # Test email body
    assert msg.is_multipart()
    
    # Find HTML part
    html_part = None
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            html_part = part.get_payload(decode=True).decode('utf-8')
            break
    
    assert html_part is not None
    assert "<h1>Test Email</h1>" in html_part
    assert "<p>Hello World</p>" in html_part
    
    inline_images = [p for p in msg.walk() if p.get('Content-ID')]
    assert len(inline_images) == 1
    assert '<img.png>' in inline_images[0].get('Content-ID')
