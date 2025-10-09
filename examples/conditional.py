from datetime import datetime
import os
from dotenv import load_dotenv
import redmail
import random

import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
from data_polars import sp500


load_dotenv()
gmail_address = os.environ["GMAIL_ADDRESS"]
gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]


email_subject = "Report on Cars"

# Randomly select 10 sequential days
num_rows = sp500.shape[0]
if num_rows < 10:
    raise ValueError("sp500 must have at least 10 rows")
start_idx = random.randint(0, num_rows - 10)
df_slice = sp500.slice(start_idx, 10).reverse()

# Compare first and last closing prices
first_close = df_slice[0, "close"]
last_close = df_slice[-1, "close"]
bg_color = "#fbeaea" if first_close > last_close else "#e6f4ea"  # red if first > last, green otherwise

intro = """
<div style='font-family: sans-serif; font-size: 1.05em; color: #222; margin-bottom: 1em;'>
    <h2 style='color: #0074D9; margin-top: 0;'>Welcome to Your S&P 500 Mini Report!</h2>
    <p>Hi there,<br><br>
    Here's a quick look at 10 sequential days from the S&P 500. The table background color reflects whether the closing price increased (green) or decreased (red) over the period.</p>
</div>
"""
salutation = """
<div style='font-family: sans-serif; font-size: 1em; color: #444; margin-top: 2em;'>
    <p>Thanks for reading!<br>Best regards,<br>Jules</p>
</div>
"""

# Render table with background color
table_html = (
    df_slice.style
    .tab_options(table_background_color=bg_color)
    .as_raw_html(inline_css=True)
)

email_body = intro + table_html + salutation

today = datetime.today()
is_weekday = today.weekday() < 5  # Monday=0, ..., Friday=4
is_monday = today.weekday() == 0

# This is here to emphasize the sender does not have to be the same as the receiver
# and the receiver list can vary
if is_weekday:
    if is_monday:
        email_receivers = [gmail_address, gmail_address, gmail_address]
    else:
        email_receivers = [gmail_address, gmail_address]
else:
    email_receivers = [gmail_address]
    

redmail.gmail.username = gmail_address
redmail.gmail.password = gmail_app_password

redmail.gmail.send(
    subject=email_subject,
    receivers=email_receivers,
    html=email_body,
)
