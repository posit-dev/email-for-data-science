from __future__ import annotations
import base64

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

import mimetypes
from email.mime.base import MIMEBase
from email import encoders

from .ingress import _read_quarto_email_json

from .structs import IntermediateEmail

__all__ = [
    "send_quarto_email_with_gmail",
    "send_intermediate_email_with_gmail",
    "send_intermediate_email_with_redmail",
    "send_intermediate_email_with_yagmail",
    "send_intermediate_email_with_mailgun",
    "send_intermediate_email_with_smtp",
]


# what to return?
# consider malformed request?
def send_quarto_email_with_gmail(
    username: str,
    password: str,
    json_path: str,
    recipients: list[str],
):
    """
    End to end sending of quarto meta data
    """
    i_email: IntermediateEmail = _read_quarto_email_json(json_path)
    i_email.recipients = recipients
    send_intermediate_email_with_gmail(
        username=username, password=password, i_email=i_email
    )


### Methods to send the email from the intermediate data structure with different services ###


# Could also take creds object
def send_intermediate_email_with_gmail(
    username: str, password: str, i_email: IntermediateEmail
):
    """
    Send the email struct content via gmail with smptlib
    """
    # Compose the email
    msg = MIMEMultipart("related")
    msg["Subject"] = i_email.subject
    msg["From"] = username
    msg["To"] = ", ".join(i_email.recipients)  # Header must be a string

    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(i_email.html, "html"))

    # Attach the plaintext
    if i_email.text:
        msg_alt.attach(MIMEText(i_email.text, "plain"))

    # Attach inline images
    for image_name, image_base64 in i_email.inline_attachments.items():
        img_bytes = base64.b64decode(image_base64)
        img = MIMEImage(img_bytes, _subtype="png", name=f"{image_name}")

        img.add_header("Content-ID", f"<{image_name}>")
        img.add_header("Content-Disposition", "inline", filename=f"{image_name}")

        msg.attach(img)

    # Attach external files (any type)
    for filename in i_email.external_attachments:
        with open(filename, "rb") as f:
            file_data = f.read()

        # Guess MIME type based on file extension
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            mime_type = "application/octet-stream"
        main_type, sub_type = mime_type.split("/", 1)

        part = MIMEBase(main_type, sub_type)
        part.set_payload(file_data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(username, password)
        server.sendmail(msg["From"], i_email.recipients, msg.as_string())


def send_intermediate_email_with_redmail(i_email: IntermediateEmail):
    pass


def send_intermediate_email_with_yagmail(i_email: IntermediateEmail):
    pass


def send_intermediate_email_with_mailgun(i_email: IntermediateEmail):
    pass


def send_intermediate_email_with_smtp(i_email: IntermediateEmail):
    pass
