from __future__ import annotations
import base64

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

import mimetypes
from email.mime.base import MIMEBase
from email import encoders
from typing import Literal

from .ingress import quarto_json_to_intermediate_email

from .structs import IntermediateEmail
import warnings

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
    Send an email using Gmail with content from a Quarto metadata JSON file.

    Parameters
    ----------
    username
        Gmail account username for sending the email

    password
        Gmail app password

    json_path
        Path to the Quarto-generated .output_metadata.json file

    recipients
        List of email addresses to send the email to

    Returns
    -------
    None
        The function sends an email but doesn't return a value

    Examples
    --------
    ```python
    send_quarto_email_with_gmail(
        "user@gmail.com",
        "password123",
        "path/to/output_metadata.json",
        ["recipient1@example.com", "recipient2@example.com"]
    )
    ```
    """
    i_email: IntermediateEmail = quarto_json_to_intermediate_email(json_path)
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
    Send an Intermediate Email object via Gmail.

    Parameters
    ----------
    username
        Gmail account username for sending the email

    password
        Gmail app password

    i_email
        IntermediateEmail object containing the email content and attachments

    Returns
    -------
    None
        The function sends an email but doesn't return a value

    Examples
    --------
    ```python
    email = IntermediateEmail(
        html="<p>Hello world</p>",
        subject="Test Email",
        recipients=["user@example.com"],
    )

    send_intermediate_email_with_gmail("user@gmail.com", "password123", email)
    ```
    """
    # Compose the email
    return send_intermediate_email_with_smtp(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username=username,
        password=password,
        i_email=i_email,
        security="tls",
    )


def send_intermediate_email_with_redmail(i_email: IntermediateEmail):
    """
    Send an Intermediate Email object via Redmail.

    Parameters
    ----------
    i_email
        IntermediateEmail object containing the email content and attachments

    Returns
    -------
    None

    Notes
    -----
    This function is a placeholder and has not been implemented yet.
    """
    raise NotImplementedError


def send_intermediate_email_with_yagmail(i_email: IntermediateEmail):
    """
    Send an Intermediate Email object via Yagmail.

    Parameters
    ----------
    i_email
        IntermediateEmail object containing the email content and attachments

    Returns
    -------
    None

    Notes
    -----
    This function is a placeholder and has not been implemented yet.
    """

    raise NotImplementedError


def send_intermediate_email_with_mailgun(i_email: IntermediateEmail):
    """
    Send an Intermediate Email object via Mailgun.

    Parameters
    ----------
    i_email
        IntermediateEmail object containing the email content and attachments

    Returns
    -------
    None

    Notes
    -----
    This function is a placeholder and has not been implemented yet.
    """
    raise NotImplementedError


def send_intermediate_email_with_smtp(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    i_email: IntermediateEmail,
    security: str = Literal["tls", "ssl", "smtp"]
):
    """
    Send an Intermediate Email object via SMTP.

    Parameters
    ----------
    smtp_host
        SMTP server hostname (e.g., "smtp.example.com")

    smtp_port
        SMTP server port (typically 587 for TLS, 465 for SSL, 25 for plain SMTP)

    username
        SMTP account username for authentication

    password
        SMTP account password

    i_email
        IntermediateEmail object containing the email content and attachments

    security
        Security protocol to use: "tls" (STARTTLS), "ssl" (SSL/TLS), or "smtp" (plain SMTP).
        Default is "tls".

    Returns
    -------
    None
        The function sends an email but doesn't return a value

    Raises
    ------
    ValueError
        If security parameter is not one of "tls", "ssl", or "smtp"

    Examples
    --------
    ```python
    email = IntermediateEmail(
        html="<p>Hello world</p>",
        subject="Test Email",
        recipients=["user@example.com"],
    )

    # TLS connection (port 587) - recommended
    send_intermediate_email_with_smtp(
        "smtp.example.com",
        587,
        "user@example.com",
        "password123",
        email,
        security="tls"
    )

    # SSL connection (port 465)
    send_intermediate_email_with_smtp(
        "smtp.example.com",
        465,
        "user@example.com",
        "password123",
        email,
        security="ssl"
    )

    # Plain SMTP (port 25) - insecure, for testing only
    send_intermediate_email_with_smtp(
        "127.0.0.1",
        8025,
        "test@example.com",
        "password",
        email,
        security="smtp"
    )
    ```
    """
    if security not in ("tls", "ssl", "smtp"):
        raise ValueError(f"security must be 'tls', 'ssl', or 'smtp', got '{security}'")

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
    if i_email.inline_attachments:
        for image_name, image_base64 in i_email.inline_attachments.items():
            img_bytes = base64.b64decode(image_base64)
            img = MIMEImage(img_bytes, _subtype="png", name=f"{image_name}")

            img.add_header("Content-ID", f"<{image_name}>")
            img.add_header("Content-Disposition", "inline", filename=f"{image_name}")

            msg.attach(img)

    # Attach external files (any type)
    if i_email.external_attachments:
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

    # Send via SMTP with appropriate security protocol
    if security == "ssl":
        # Use SSL/TLS from the start (typically port 465)
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(username, password)
            server.sendmail(msg["From"], i_email.recipients, msg.as_string())
    elif security == "tls":
        # Use STARTTLS - start unencrypted then upgrade (typically port 587)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(msg["From"], i_email.recipients, msg.as_string())
    else:  # security == "smtp"
        warnings.warn(
            "You are sending email without encryption (plain SMTP). This is insecure and not recommended for production use.",
            UserWarning,
        )
        # Plain SMTP without encryption (insecure - for testing only)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            # Try to login, but don't fail if server doesn't require it
            try:
                server.login(username, password)
            except smtplib.SMTPException:
                pass  # Test servers may not require authentication
            server.sendmail(msg["From"], i_email.recipients, msg.as_string())
