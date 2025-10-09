## TODO: work in progress

from dotenv import load_dotenv
import os
import base64
import json

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib


load_dotenv()

password = os.environ["GMAIL_APP_PASSWORD"]
username = "jules.walzergoldfeld@gmail.com"

with open(".output_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# Get email content (if present)
email_content = metadata.get("rsc_email_body_html", "")

# Get email images (dictionary: {filename: base64_string})
email_images = metadata.get("rsc_email_images", {})

# Compose the email
msg = MIMEMultipart("related")
msg["Subject"] = "hello world"
msg["From"] = username
msg["To"] = username

msg_alt = MIMEMultipart("alternative")
msg.attach(msg_alt)
msg_alt.attach(MIMEText(email_content, "html"))

# Attach images
for image_name, image_base64 in email_images.items():
    img_bytes = base64.b64decode(image_base64)
    img = MIMEImage(img_bytes, _subtype="png")
    img.add_header('Content-ID', f'<{image_name}>')
    msg.attach(img)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(username, password)
    server.sendmail(msg["From"], [msg["To"]], msg.as_string())