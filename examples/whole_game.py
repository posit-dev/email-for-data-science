import os
from dotenv import load_dotenv
from data_polars import sp500
import redmail

load_dotenv()
gmail_address = os.environ["GMAIL_ADDRESS"]
gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]


email_subject = "Report on Cars"
email_body = sp500.head(10).style.as_raw_html(inline_css=True)

# This is here to emphasize the sender does not have to be the same as the receiver
email_receiver = gmail_address  

redmail.gmail.username = gmail_address
redmail.gmail.password = gmail_app_password

redmail.gmail.send(
    subject=email_subject,
    receivers=[email_receiver],
    html=email_body,
)
