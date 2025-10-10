## TODO: work in progress

from dataclasses import dataclass
import base64
import json

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

from email.message import EmailMessage


@dataclass
class IntermediateDataStruct:
    html: str
    attachments: dict[str, str]
    subject: str
    rsc_email_supress_report_attachment: bool
    rsc_email_supress_scheduled: bool

    text: str = None  # sometimes present in quarto
    recipients: list[str] = None  # not present in quarto


# You will have to call redmail get_message, and pass that EmailMessage object to this
# It feels wrong to deconstruct a mime multipart email message.
# Why not just send the original payload?
# Or make the intermediate struct hold that payload (the EmailMessage class)
def redmail_to_intermediate_struct(msg: EmailMessage) -> IntermediateDataStruct:
    email_body = msg.get_body()
    attachments = {}
    # maybe do walk
    for elem in msg.iter_attachments():
        if elem.is_attachment():
            # This can fail if there's no associated filename?
            attachments[elem.get_filename()] = elem.get_content()


    iStruct = IntermediateDataStruct(html=email_body)

    return iStruct



def yagmail_to_intermediate_struct():
    pass


def mjml_to_intermediate_struct():
    ## This will require 2 steps:
    # 1. mjml2html
    # 2. pulling attachments out
    pass


# Some Connect handling happens here: https://github.com/posit-dev/connect/blob/c84f845f9e75887f6450b32f1071e57e8777b8b1/src/connect/reports/output_metadata.go
# Helper method to parse the quarto JSON
def _read_quarto_email_json(path: str) -> IntermediateDataStruct:
    with open(path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    email_html = metadata.get("rsc_email_body_html", "")
    email_subject = metadata.get("rsc_email_subject", "")
    email_text = metadata.get("rsc_email_body_text", "")

    # Other metadata fields, as per https://github.com/posit-dev/connect/wiki/Rendering#output-metadata-fields-and-validation
    # These might be rmd specific, not quarto
    # metadata.get("rsc_output_files", [])
    # metadata.get("rsc_email_attachments", [])

    # Get email images (dictionary: {filename: base64_string})
    email_images = metadata.get("rsc_email_images", {})

    supress_report_attachment = metadata.get(
        "rsc_email_supress_report_attachment", False
    )
    supress_scheduled = metadata.get("rsc_email_supress_scheduled", False)

    iStruct = IntermediateDataStruct(
        html=email_html,
        text=email_text,
        attachments=email_images,
        subject=email_subject,
        rsc_email_supress_report_attachment=supress_report_attachment,
        rsc_email_supress_scheduled=supress_scheduled,
    )

    return iStruct

# what to return?
# consider malformed request?

def send_quarto_email_with_gmail(
    username: str,
    password: str,
    json_path: str,
    recipients: list[str],
):
    '''
    End to end sending of quarto meta data
    '''
    email_struct: IntermediateDataStruct = _read_quarto_email_json(json_path)
    email_struct.recipients = recipients
    send_struct_email_with_gmail(
        username=username, password=password, email_struct=email_struct
    )


### Methods to send the email from the intermediate data structure with different services ###


# Could also take creds object
def send_struct_email_with_gmail(
    username: str, password: str, email_struct: IntermediateDataStruct
):
    '''
    Send the email struct content via gmail with smptlib
    '''
    # Compose the email
    msg = MIMEMultipart("related")
    msg["Subject"] = email_struct.subject
    msg["From"] = username
    msg["To"] = ", ".join(email_struct.recipients)  # Header must be a string

    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(email_struct.html, "html"))

    # Attach the plaintext
    if email_struct.text:
        msg_alt.attach(MIMEText(email_struct.text, "plain"))

    # Attach images
    for image_name, image_base64 in email_struct.attachments.items():
        img_bytes = base64.b64decode(image_base64)
        img = MIMEImage(img_bytes, _subtype="png", name=f"{image_name}")

        img.add_header('Content-ID', f'<{image_name}>')
        img.add_header("Content-Disposition", "inline", filename=f"{image_name}") 

        msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(username, password)
        server.sendmail(msg["From"], email_struct.recipients, msg.as_string())


def send_struct_email_with_redmail(email_struct: IntermediateDataStruct):
    
    pass

def send_struct_email_with_yagmail(email_struct: IntermediateDataStruct):
    pass

def send_struct_email_with_mailgun(email_struct: IntermediateDataStruct):
    pass