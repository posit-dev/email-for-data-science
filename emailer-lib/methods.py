## TODO: work in progress
from __future__ import annotations
from dataclasses import dataclass
import base64
import json
import re


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

from email.message import EmailMessage
from mjml import mjml2html
import mimetypes
from email.mime.base import MIMEBase
from email import encoders


@dataclass
class IntermediateEmail:
    html: str
    subject: str
    rsc_email_supress_report_attachment: bool
    rsc_email_supress_scheduled: bool

    # is a list of files in path from current directory
    external_attachments: list[str] | None = None

    # has structure {filename: base64_string}
    inline_attachments: dict[str, str] | None = None

    text: str | None = None  # sometimes present in quarto
    recipients: list[str] | None = None  # not present in quarto

    def write_preview_email(self, out_file: str = "preview_email.html") -> None:
        html_with_inline = re.sub(
            r'src="cid:([^"\s]+)"',
            _add_base_64_to_inline_attachments(self.inline_attachments),
            self.html,
        )

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html_with_inline)

        if self.external_attachments:
            raise ValueError("Preview does not yet support external attachments.")

    def write_email_message(self) -> EmailMessage:
        pass

    # sends just to some preview recipient?
    def preview_send_email():
        pass


def redmail_to_intermediate_email(msg: EmailMessage) -> IntermediateEmail:
    # We will have to call redmail's get_message, and pass that EmailMessage object to this
    return _email_message_to_intermediate_email(msg)


def yagmail_to_intermediate_email():
    pass


def mjml_to_intermediate_email(mjml_content: str) -> IntermediateEmail:
    email_content = mjml2html(mjml_content)

    # Find all <img> tags and extract their src attributes
    pattern = r'<img[^>]+src="([^"\s]+)"[^>]*>'
    matches = re.findall(pattern, email_content)
    inline_attachments = {}
    for src in matches:
        # in theory, retrieve the externally hosted images and save to bytes
        # the user would need to pass CID-referenced images directly somehow,
        # as mjml doesn't handle them
        raise NotImplementedError("mj-image tags are not yet supported")

    i_email = IntermediateEmail(
        html=email_content,
        subject="",
        rsc_email_supress_report_attachment=False,
        rsc_email_supress_scheduled=False,
        inline_attachments=inline_attachments,
    )

    return i_email


# Some Connect handling happens here: https://github.com/posit-dev/connect/blob/c84f845f9e75887f6450b32f1071e57e8777b8b1/src/connect/reports/output_metadata.go
# Helper method to parse the quarto JSON
def _read_quarto_email_json(path: str) -> IntermediateEmail:
    with open(path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    email_html = metadata.get("rsc_email_body_html", "")
    email_subject = metadata.get("rsc_email_subject", "")
    email_text = metadata.get("rsc_email_body_text", "")

    # Other metadata fields, as per https://github.com/posit-dev/connect/wiki/Rendering#output-metadata-fields-and-validation
    # These might be rmd specific, not quarto
    
    # This is a list of paths that connect dumps attached files into.
    # Should be in same output directory
    output_files = metadata.get("rsc_output_files", [])
    output_files += metadata.get("rsc_email_attachments", [])
    
    # Get email images (dictionary: {filename: base64_string})
    email_images = metadata.get("rsc_email_images", {})

    supress_report_attachment = metadata.get(
        "rsc_email_supress_report_attachment", False
    )
    supress_scheduled = metadata.get("rsc_email_supress_scheduled", False)

    i_email = IntermediateEmail(
        html=email_html,
        text=email_text,
        inline_attachments=email_images,
        external_attachments=output_files,
        subject=email_subject,
        rsc_email_supress_report_attachment=supress_report_attachment,
        rsc_email_supress_scheduled=supress_scheduled,
    )

    return i_email


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


def write_email_message_to_file(
    msg: EmailMessage, out_file: str = "preview_email.html"
):
    """
    Writes the HTML content of an email message to a file, inlining any images referenced by Content-ID (cid).

    This function extracts all attachments referenced by Content-ID from the given EmailMessage,
    replaces any `src="cid:..."` references in the HTML body with base64-encoded image data,
    and writes the resulting HTML to the specified output file.

    Params:
        msg (EmailMessage): The email message object containing the HTML body and attachments.
        out_file (str, optional): The path to the output HTML file. Defaults to "preview_email.html".

    Returns:
        None
    """
    inline_attachments = {}

    for part in msg.walk():
        content_id = part.get("Content-ID")
        if content_id:
            cid = content_id.strip("<>")

            payload = part.get_payload(decode=True)
            inline_attachments[cid] = payload

    html = msg.get_body(preferencelist=("html")).get_content()

    # Replace each cid reference with base64 data
    html_inline = re.sub(
        r'src="cid:([^"]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    # Write to file
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_inline)

# useful because redmail bundles an email message... may help in other cases too
def _email_message_to_intermediate_email(msg: EmailMessage) -> IntermediateEmail:
    # It feels wrong to deconstruct a mime multipart email message.
    # Why not just send the original payload?
    # Or make the intermediate struct hold that payload (the EmailMessage class)

    # Extract subject
    subject = msg.get('Subject', '')

    # Extract recipients (To, Cc, Bcc)
    # Recipients get flattened to one list. Maybe in the future we keep these 3 separate?
    recipients = []
    for header in ['To', 'Cc', 'Bcc']:
        value = msg.get(header)
        if value:
            recipients += [addr.strip() for addr in value.split(',') if addr.strip()]
    recipients = recipients if recipients else None

    # Extract HTML and plain text bodies
    html = None
    text = None

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get_content_disposition()
            if ctype == 'text/html' and disp != 'attachment':
                html = part.get_content()
            elif ctype == 'text/plain' and disp != 'attachment':
                text = part.get_content()
    else:
        ctype = msg.get_content_type()
        if ctype == 'text/html':
            html = msg.get_content()
        elif ctype == 'text/plain':
            text = msg.get_content()

    # Extract inline attachments (images with Content-ID)
    inline_attachments = {}
    external_attachments = []
    for part in msg.iter_attachments():
        filename = part.get_filename()
        content_id = part.get('Content-ID')
        payload = part.get_payload(decode=True)
        if content_id:
            cid = content_id.strip('<>')
            # Store as base64 string
            inline_attachments[cid] = base64.b64encode(payload).decode('utf-8')
        elif filename:
            # Save filename for external attachments
            # Not certain that all attached files have associated filenames
            external_attachments.append(filename)

    return IntermediateEmail(
        html=html or "",
        subject=subject,
        external_attachments=external_attachments if external_attachments else None,
        inline_attachments=inline_attachments if inline_attachments else None,
        text=text,
        recipients=recipients,
    )


# TODO: make sure this is not losing other attributes of the inline attachments
def _add_base_64_to_inline_attachments(inline_attachments: dict[str, str]):
    # Replace all src="cid:..." in the HTML
    def replace_cid(match):
        cid = match.group(1)
        img_data = inline_attachments.get(cid)
        if img_data:
            # TODO: this is kinda hacky
            # If it's a string, decode from base64 to bytes first
            if isinstance(img_data, str):
                try:
                    img_bytes = base64.b64decode(img_data)
                except Exception:
                    # If not base64, treat as raw bytes
                    img_bytes = img_data.encode("utf-8")
            else:
                img_bytes = img_data
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            return f'src="data:image;base64,{b64}"'
        return match.group(0)

    return replace_cid
