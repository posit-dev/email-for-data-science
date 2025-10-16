from __future__ import annotations
from base64 import b64encode
import json
import re

from email.message import EmailMessage
from mjml import mjml2html

from .structs import IntermediateEmail

__all__ = [
    "redmail_to_intermediate_email",
    "yagmail_to_intermediate_email",
    "mjml_to_intermediate_email",
    "quarto_json_to_intermediate_email",
]


def redmail_to_intermediate_email(msg: EmailMessage) -> IntermediateEmail:
    """
    Convert a Redmail EmailMessage object to an IntermediateEmail

    Params
    ------
    msg
        The Redmail-generated EmailMessage object

    Converts the input EmailMessage to the intermediate email structure
    """
    return _email_message_to_intermediate_email(msg)


def yagmail_to_intermediate_email():
    """
    Convert a Yagmail email object to an IntermediateEmail

    Params
    ------
    (none)

    Not yet implemented
    """
    pass


def mjml_to_intermediate_email(mjml_content: str) -> IntermediateEmail:
    """
    Convert MJML markup to an IntermediateEmail

    Params
    ------
    mjml_content
        MJML markup string

    Converts MJML markup to the intermediate email structure
    """
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


# useful because redmail bundles an email message... may help in other cases too
def _email_message_to_intermediate_email(msg: EmailMessage) -> IntermediateEmail:
    """
    Convert a Python EmailMessage object to an IntermediateEmail

    Params
    ------
    msg
        The email message to convert

    Converts the input EmailMessage to the intermediate email structure
    """
    # It feels wrong to deconstruct a mime multipart email message.
    # Why not just send the original payload?
    # Or make the intermediate struct hold that payload (the EmailMessage class)

    # Extract subject
    subject = msg.get("Subject", "")

    # Extract recipients (To, Cc, Bcc)
    # Recipients get flattened to one list. Maybe in the future we keep these 3 separate?
    recipients = []
    for header in ["To", "Cc", "Bcc"]:
        value = msg.get(header)
        if value:
            recipients += [addr.strip() for addr in value.split(",") if addr.strip()]
    recipients = recipients if recipients else None

    # Extract HTML and plain text bodies
    html = None
    text = None

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get_content_disposition()
            if ctype == "text/html" and disp != "attachment":
                html = part.get_content()
            elif ctype == "text/plain" and disp != "attachment":
                text = part.get_content()
    else:
        ctype = msg.get_content_type()
        if ctype == "text/html":
            html = msg.get_content()
        elif ctype == "text/plain":
            text = msg.get_content()

    # Extract inline attachments (images with Content-ID)
    inline_attachments = {}
    external_attachments = []
    for part in msg.iter_attachments():
        filename = part.get_filename()
        content_id = part.get("Content-ID")
        payload = part.get_payload(decode=True)
        if content_id:
            cid = content_id.strip("<>")
            # Store as base64 string
            inline_attachments[cid] = b64encode(payload).decode("utf-8")
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


# Some Connect handling happens here: https://github.com/posit-dev/connect/blob/c84f845f9e75887f6450b32f1071e57e8777b8b1/src/connect/reports/output_metadata.go
# Helper method to parse the quarto JSON
def quarto_json_to_intermediate_email(path: str) -> IntermediateEmail:
    """
    Convert a Quarto output metadata JSON file to an IntermediateEmail

    Params
    ------
    path
        Path to the Quarto output metadata JSON file

    Converts the Quarto output metadata to the intermediate email structure
    """
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
