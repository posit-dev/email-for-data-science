import os
from dotenv import load_dotenv
import redmail

# import sys
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from data_polars import sp500


load_dotenv()
gmail_address = os.environ["GMAIL_ADDRESS"]
gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]


email_subject = "Report on Cars"
email_body = sp500.head(10).style.as_raw_html(inline_css=True)

intro = """
<div style='font-family: sans-serif; font-size: 1.05em; color: #222; margin-bottom: 1em;'>
    <h2 style='color: #0074D9; margin-top: 0;'>Welcome to Your S&P 500 Mini Report!</h2>
    <p>Hi there,<br><br>
    Here’s a quick look at the latest data from the S&P 500. Explore the table below to see some of the most recent entries and get a feel for the market’s pulse.</p>
</div>
"""
salutation = """
<div style='font-family: sans-serif; font-size: 1em; color: #444; margin-top: 2em;'>
    <p>Thanks for reading!<br>Best regards,<br>Jules</p>
</div>
"""
table_html = sp500.head(10).style.as_raw_html(inline_css=True)

email_body = intro + table_html + salutation

# This is here to emphasize the sender does not have to be the same as the receiver
email_receiver = gmail_address  

redmail.gmail.username = gmail_address
redmail.gmail.password = gmail_app_password

redmail.gmail.send(
    subject=email_subject,
    receivers=[gmail_address],
    html=email_body,
)
