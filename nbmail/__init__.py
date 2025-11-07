from .ingress import (
    redmail_to_email,
    yagmail_to_email,
    mjml_to_email,
    quarto_json_to_email,
)

from .egress import (
    send_quarto_email_with_gmail,
    send_email_with_gmail,
    send_email_with_redmail,
    send_email_with_yagmail,
    send_email_with_mailgun,
    send_email_with_smtp,
)

from .utils import write_email_message_to_file

from .structs import Email


__all__ = [
    "quarto_json_to_email",
    "Email",
    "redmail_to_email",
    "yagmail_to_email",
    "mjml_to_email",
    "send_quarto_email_with_gmail",
    "send_email_with_gmail",
    "send_email_with_redmail",
    "send_email_with_yagmail",
    "send_email_with_mailgun",
    "send_email_with_smtp",
    "write_email_message_to_file",
]
