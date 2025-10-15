from .ingress import (
    redmail_to_intermediate_email,
    yagmail_to_intermediate_email,
    mjml_to_intermediate_email,
)

from .egress import (
    send_quarto_email_with_gmail,
    send_intermediate_email_with_gmail,
    send_intermediate_email_with_redmail,
    send_intermediate_email_with_yagmail,
    send_intermediate_email_with_mailgun,
    send_intermediate_email_with_smtp,
)

from utils import write_email_message_to_file

from .structs import IntermediateEmail


__all__ = [
    "IntermediateEmail",
    "redmail_to_intermediate_email",
    "yagmail_to_intermediate_email",
    "mjml_to_intermediate_email",
    "send_quarto_email_with_gmail",
    "send_intermediate_email_with_gmail",
    "send_intermediate_email_with_redmail",
    "send_intermediate_email_with_yagmail",
    "send_intermediate_email_with_mailgun",
    "send_intermediate_email_with_smtp",
    "write_email_message_to_file",
]
