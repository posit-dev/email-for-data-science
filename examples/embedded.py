from io import BytesIO
import os
from dotenv import load_dotenv

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

# import sys
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from data_polars import sp500
import polars as pl
from plotnine import (
    ggplot,
    aes,
    geom_line,
    geom_point,
    labs,
    theme_minimal,
    theme,
    element_text,
    scale_x_datetime,
    geom_bar,
)

df = sp500.head(250)

df = df.with_columns([pl.col("close").rolling_mean(window_size=20).alias("ma20")])
df = df.with_columns([pl.col("date").str.strptime(pl.Date, "%Y-%m-%d", strict=False)])
df = df.drop_nulls()
plot = (
    ggplot(df, aes(x="date", y="close"))
    + geom_line(color="#0074D9", size=1.2, alpha=0.8)
    + geom_line(aes(y="ma20"), color="#2ECC40", size=1, linetype="dashed")
    + geom_point(color="#FF4136", size=1, alpha=0.5)
    + labs(
        title="S&P 500 Closing Prices with 20-Day Moving Average in 2015",
        x="Date",
        y="Close",
    )
    + scale_x_datetime(date_breaks="1 month", date_labels="%b %Y")
    + theme_minimal()
    + theme(
        axis_text_x=element_text(rotation=45, ha="right", size=9),
        axis_text_y=element_text(size=9),
        plot_title=element_text(size=14, weight="bold"),
    )
)

buf = BytesIO()
plot.save(buf, format="png")
buf.seek(0)
plot1_bytes = buf.read()

df_monthly = (
    df.with_columns(
        [
            pl.col("date")
            .dt.strftime("%Y-%m")  # Extract year-month string
            .alias("year_month")
        ]
    )
    .group_by("year_month")
    .agg([pl.col("volume").mean().alias("avg_volume")])
    .sort("year_month")
)

df_monthly = df_monthly.with_columns(
    [(pl.col("avg_volume") / 1e9).alias("avg_volume_billion")]
)

hist_plot = (
    ggplot(df_monthly, aes(x="year_month", y="avg_volume_billion"))
    + geom_bar(stat="identity", fill="#0074D9", alpha=0.8, width=0.7)
    + labs(
        title="Average Daily Trades per Month", x="Month", y="Average Volume (Billions)"
    )
    + theme_minimal()
    + theme(
        axis_text_x=element_text(rotation=45, ha="right", size=9),
        axis_text_y=element_text(size=9),
        plot_title=element_text(size=13, weight="bold"),
    )
)

buf2 = BytesIO()
hist_plot.save(buf2, format="png")
buf2.seek(0)
plot2_bytes = buf2.read()

plot1_html = """
<div style="text-align:center;">
  <img src="cid:plot1" style="width:400px; max-width:90%; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.08);"/>
</div>
<br>"""

plot2_html = """
<div style="text-align:center;">
  <img src="cid:plot2" style="width:400px; max-width:90%; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.08);"/>
</div>
<br>"""

button_html = """
<div style="text-align:center; margin-top: 1.5em;">
  <a href="https://posit-dev.github.io/great-tables/reference/data.sp500.html#great_tables.data.sp500"
     style="
       display: inline-block;
       padding: 0.7em 1.5em;
       font-size: 1em;
       color: #fff;
       background-color: #0074D9;
       border: none;
       border-radius: 6px;
       text-decoration: none;
       box-shadow: 0 2px 6px rgba(0,0,0,0.07);
       transition: background 0.2s;
     "
     target="_blank"
     >Check out the data</a>
</div>
"""

body_text = f"""
<div style="font-family: sans-serif; font-size: 1.05em; color: #222; background: #f8f9fa; border-radius: 10px; padding: 1.5em; border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
  <h2 style="color: #0074D9; margin-top: 0;">S&P 500 Report</h2>
  <p>
    Hello Jules,<br><br>
    Here is a recent plot of S&P 500 closing prices with a 20-day moving average.<br>
    Below, you can also see the average daily trades per month.<br>
    For more details, check out the data source.
  </p>
  <div style="text-align: center;">
    <div style="display: inline-flex; justify-content: center; gap: 2em; flex-wrap: wrap;">
      <div style="flex: 1 1 350px; text-align: center;">{plot1_html}</div>
      <div style="flex: 1 1 350px; text-align: center;">{plot2_html}</div>
    </div>
  </div>
  {button_html}
  <p style="margin-top:2em; color:#444; font-size:1em;">Thank you for reading this report. If you have any questions or would like to discuss the data further, feel free to reply to this email.<br><br>Best regards,<br>Jules</p>
</div>
"""

html_head = """
<meta charset="utf-8">
<title>Email Preview</title>
"""

email_content = f"""<!doctype html>
<html>
  <head>
  {html_head}
  </head>
  <body>
{body_text}
  </body>
</html>"""

load_dotenv()
gmail_address = os.environ["GMAIL_ADDRESS"]
gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
email_subject = "Report on the S&P 500"

msg = MIMEMultipart("related")
msg["Subject"] = email_subject
msg["From"] = gmail_address
msg["To"] = gmail_address

msg_alt = MIMEMultipart("alternative")
msg.attach(msg_alt)
msg_alt.attach(MIMEText(email_content, "html"))

# Attach images
img = MIMEImage(plot1_bytes, _subtype="png")
img.add_header("Content-ID", "<plot1>")
msg.attach(img)

img2 = MIMEImage(plot2_bytes, _subtype="png")
img2.add_header("Content-ID", "<plot2>")
msg.attach(img2)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(gmail_address, gmail_app_password)
    server.sendmail(msg["From"], [msg["To"]], msg.as_string())
