from io import BytesIO
import os
from dotenv import load_dotenv

from mjml import mjml2html

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

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

mjml_content = """
<mjml><mj-head><mj-title>Discount Light</mj-title>
    <mj-preview>Pre-header Text</mj-preview>
    <mj-attributes><mj-all font-family="'Helvetica Neue', Helvetica, Arial, sans-serif"></mj-all>
      <mj-text font-weight="400" font-size="16px" color="#000000" line-height="24px" font-family="'Helvetica Neue', Helvetica, Arial, sans-serif"></mj-text></mj-attributes>
    <mj-style inline="inline">.body-section {
      -webkit-box-shadow: 1px 4px 11px 0px rgba(0, 0, 0, 0.15);
      -moz-box-shadow: 1px 4px 11px 0px rgba(0, 0, 0, 0.15);
      box-shadow: 1px 4px 11px 0px rgba(0, 0, 0, 0.15);
      }</mj-style>
    <mj-style inline="inline">.text-link {
      color: #5e6ebf
      }</mj-style>
    <mj-style inline="inline">.footer-link {
      color: #888888
      }</mj-style></mj-head>
  <mj-body background-color="#E7E7E7" width="600px"><mj-section full-width="full-width" background-color="#040B4F" padding-bottom="0px"><mj-column width="100%"><mj-image src="https://static.mailjet.com/mjml-website/templates/austin-logo.png" alt="" align="center" width="150px"></mj-image>
        <mj-text color="#ffffff" font-weight="bold" align="center" text-transform="uppercase" font-size="16px" letter-spacing="1px" padding-top="30px">Austin, TX
          <br />
          <span style="color: #979797; font-weight: normal">-</span></mj-text>
        <mj-text color="#17CBC4" align="center" font-size="13px" padding-top="0" font-weight="bold" text-transform="uppercase" letter-spacing="1px" line-height="20px">Austin Convention Center
          <br />
          123 Main Street, 78701</mj-text>
        <mj-image src="https://static.mailjet.com/mjml-website/templates/austin-header-top.png" width="600px" alt="" padding="0px" href="https://google.com"></mj-image></mj-column></mj-section>
    <mj-section background-color="#1f2e78"><mj-column width="100%"><mj-image src="https://static.mailjet.com/mjml-website/templates/austin-header-bottom.png" width="600px" alt="" padding="0px" href="https://google.com"></mj-image></mj-column></mj-section>
    <mj-wrapper padding-top="0" padding-bottom="0px" css-class="body-section"><mj-section background-color="#ffffff" padding-left="15px" padding-right="15px"><mj-column width="100%"><mj-text color="#212b35" font-weight="bold" font-size="20px">Croft's in Austin is opening December 20th</mj-text>
          <mj-text color="#637381" font-size="16px">Hi Jane,</mj-text>
          <mj-text color="#637381" font-size="16px">Lorem ipsum, dolor sit amet consectetur adipisicing elit. Quia a assumenda nulla in quisquam optio quibusdam fugiat perspiciatis nobis, ad tempora culpa porro labore. Repudiandae accusamus obcaecati voluptatibus accusantium perspiciatis.</mj-text>
          <mj-text color="#637381" font-size="16px">Tempora culpa porro labore. Repudiandae accusamus obcaecati voluptatibus accusantium perspiciatis:</mj-text>
          <mj-text color="#637381" font-size="16px">
            <ul>
              <li style="padding-bottom: 20px"><strong>Lorem ipsum dolor:</strong> Sit amet consectetur adipisicing elit.</li>
              <li style="padding-bottom: 20px"><strong>Quia a assumenda nulla:</strong> Repudiandae accusamus obcaecati voluptatibus accusantium perspiciatis.</li>
              <li><strong>Tempora culpa porro labore:</strong> In quisquam optio quibusdam fugiat perspiciatis nobis.</li>
            </ul>
          </mj-text>
          <mj-text color="#637381" font-size="16px" padding-bottom="30px">Lorem ipsum dolor <a class="text-link" href="https://google.com">sit amet consectetur</a> adipisicing elit. Earum eaque sunt nulla in, id eveniet quae unde ad ipsam ut, harum autem porro reiciendis minus libero illo. Vero, fugiat reprehenderit.</mj-text>
          <mj-button background-color="#5e6ebf" align="center" color="#ffffff" font-size="17px" font-weight="bold" href="https://google.com" width="300px">RSVP Today</mj-button>
          <mj-button background-color="#5e6ebf" align="center" color="#ffffff" font-size="17px" font-weight="bold" href="https://google.com" width="300px">Book an Appointment</mj-button>
          <mj-text color="#637381" font-size="16px" padding-top="30px">Lorem ipsum dolor <a class="text-link" href="https://google.com">sit amet consectetur</a> adipisicing elit. Earum eaque sunt nulla in, id eveniet quae unde ad ipsam ut, harum autem porro reiciendis minus libero illo. Vero, fugiat reprehenderit.</mj-text>
          <mj-text color="#637381" font-size="16px" padding-bottom="0px">Lorem ipsum dolor sit amet consectetur adipisicing elit.</mj-text></mj-column></mj-section>
      <mj-section background-color="#ffffff" padding-left="15px" padding-right="15px" padding-top="0"><mj-column width="50%"><mj-image align="center" src="https://static.mailjet.com/mjml-website/templates/austin-image-1.png" alt=""></mj-image></mj-column>
        <mj-column width="50%"><mj-image align="center" src="https://static.mailjet.com/mjml-website/templates/austin-image-2.png" alt=""></mj-image></mj-column></mj-section>
      <mj-section background-color="#ffffff" padding-left="15px" padding-right="15px" padding-top="0"><mj-column width="100%"><mj-divider border-color="#DFE3E8" border-width="1px"></mj-divider></mj-column></mj-section>
      <mj-section background-color="#ffffff" padding="0 15px 0 15px"><mj-column width="100%"><mj-text color="#212b35" font-weight="bold" font-size="20px" padding-bottom="0px">Come see us!</mj-text>
          <mj-text color="#637381" font-size="16px">We're looking forward to meeting you.</mj-text></mj-column></mj-section>
      <mj-section background-color="#ffffff" padding-left="15px" padding-right="15px"><mj-column width="50%"><mj-text color="#212b35" font-size="12px" text-transform="uppercase" font-weight="bold" padding-bottom="0px">address</mj-text>
          <mj-text color="#637381" font-size="14px" padding-top="0">Austin Convention Center
            <br />
            123 Main Street, 78701</mj-text></mj-column>
        <mj-column width="50%"><mj-text color="#212b35" font-size="12px" text-transform="uppercase" font-weight="bold" padding-bottom="0px">Hours of Operation</mj-text>
          <mj-text color="#637381" font-size="14px" padding-top="0">Monday, December 20th: 8:00AM - 5:00PM
            <br />
            Tuesday, December 21st: 8:00AM - 5:00PM</mj-text></mj-column></mj-section>
      <mj-section background-color="#ffffff" padding-left="15px" padding-right="15px"><mj-column width="100%"><mj-image src="https://static.mailjet.com/mjml-website/templates/austin-map.jpg" alt=""></mj-image></mj-column></mj-section></mj-wrapper>
    <mj-wrapper full-width="full-width"><mj-section><mj-column width="100%" padding="0px"><mj-social font-size="15px" icon-size="30px" mode="horizontal" padding="0px" align="center"><mj-social-element name="facebook"></mj-social-element>
            <mj-social-element name="twitter"></mj-social-element>
            <mj-social-element name="google"></mj-social-element></mj-social>
          <mj-text color="#445566" font-size="11px" font-weight="bold" align="center">View this email in your browser</mj-text>
          <mj-text color="#445566" font-size="11px" align="center" line-height="16px">You are receiving this email advertisement because you registered with Croft's Accountants. (123 Main Street, Austin, TX 78701) and agreed to receive emails from us regarding new features, events and special offers.</mj-text>
          <mj-text color="#445566" font-size="11px" align="center" line-height="16px">&copy; Croft's Accountants Inc., All Rights Reserved.</mj-text></mj-column></mj-section>
      <mj-section padding-top="0"><mj-group><mj-column width="100%" padding-right="0px"><mj-text color="#445566" font-size="11px" align="center" line-height="16px" font-weight="bold"><a class="footer-link" href="https://www.google.com">Privacy</a>&#xA0;&#xA0;&#xA0;&#xA0;&#xA0;&#xA0;&#xA0;&#xA0;<a class="footer-link" href="https://www.google.com">Unsubscribe</a></mj-text></mj-column></mj-group></mj-section></mj-wrapper></mj-body>
</mjml>
"""

email_content = mjml2html(mjml_content)

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
