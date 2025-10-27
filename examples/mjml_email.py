from io import BytesIO
import os
from dotenv import load_dotenv

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

# import sys
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from docs.data_polars import sp500
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

from mjml import mjml2html

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

mjml_content = """
<mjml>
  <mj-head>
    <mj-title>S&P 500 report</mj-title>
    <mj-preview>A subtitle that's not in the email body.</mj-preview>
    <mj-attributes>
      <mj-all font-family="'Helvetica Neue', Helvetica, Arial, sans-serif"></mj-all>
      <mj-text font-weight="400" font-size="16px" color="#000000" line-height="24px" font-family="'Helvetica Neue', Helvetica, Arial, sans-serif"></mj-text>
    </mj-attributes>
    <mj-style inline="inline">
      .body-section {
      -webkit-box-shadow: 1px 4px 11px 0px rgba(0, 0, 0, 0.15);
      -moz-box-shadow: 1px 4px 11px 0px rgba(0, 0, 0, 0.15);
      box-shadow: 1px 4px 11px 0px rgba(0, 0, 0, 0.15);
      }
    </mj-style>
    <mj-style inline="inline">
      .text-link {
      color: #5e6ebf
      }
    </mj-style>
    <mj-style inline="inline">
      .footer-link {
      color: #888888
      }
    </mj-style>

  </mj-head>
  <mj-body background-color="#E7E7E7" width="600px">
    <mj-section full-width="full-width" background-color="#040B4F" padding-bottom="0">
      <mj-column width="100%">
        <mj-text color="#ffffff" font-weight="bold" align="center" text-transform="uppercase" font-size="16px" letter-spacing="1px" padding-top="30px">
          Posit Demo
          <br />
          <span style="color: #979797; font-weight: normal">-</span>
        </mj-text>
        <mj-image src="cid:newspapers" width="600px" alt="" padding="0" href="https://google.com" />
      </mj-column>
    </mj-section>

    <mj-wrapper padding-top="0" padding-bottom="0" css-class="body-section">
      <mj-section background-color="#ffffff" padding-left="15px" padding-right="15px">
        <mj-column width="100%">
          <mj-text color="#212b35" font-weight="bold" font-size="20px">
            A report on the S&P 500
          </mj-text>
          <mj-text color="#637381" font-size="16px">
            Hi Jules,
          </mj-text>
          <mj-text color="#637381" font-size="16px">
            This report provides a fresh look at recent trends in the S&P 500 index. We’ve included visualizations of closing prices and trading volumes to help you better understand market movements.
          </mj-text>
          <mj-text color="#637381" font-size="16px">
            Whether you’re a seasoned investor or just curious about the market, these charts offer a snapshot of how the S&P 500 has performed over the past year.
          </mj-text>
          <mj-text color="#637381" font-size="16px">
            Key highlights include:
            <ul>
              <li style="padding-bottom: 20px"><strong>Price momentum:</strong> See how the 20-day moving average tracks overall trends.</li>
              <li style="padding-bottom: 20px"><strong>Trading activity:</strong> Monthly averages reveal periods of higher and lower volume.</li>
              <li><strong>Market insights:</strong> Use these visuals to spot patterns and inform your next steps.</li>
            </ul>
          </mj-text>
          <mj-text color="#637381" font-size="16px" padding-bottom="30px">
            If you have any questions or want to discuss the data further, feel free to reach out. We hope you find this report useful and engaging!
          </mj-text>
          
        </mj-column>
      </mj-section>
      <mj-section background-color="#ffffff" padding-left="15px" padding-right="15px" padding-top="0">
        <mj-column width="50%">
          <mj-image align="center" src="cid:plot1" alt="" />
        </mj-column>
        <mj-column width="50%">
          <mj-image align="center" src="cid:plot2" alt="" />
        </mj-column>
      </mj-section>
      <mj-section background-color="#ffffff" padding-left="15px" padding-right="15px" padding-top="0">
        <mj-column width="100%">
          <mj-divider border-color="#DFE3E8" border-width="1px" />
        </mj-column>
      </mj-section>
      <mj-section background-color="#ffffff" padding="0 15px 0 15px">
        <mj-column width="100%">
          <mj-text color="#212b35" font-weight="bold" font-size="20px" padding-bottom="0">
            Come see us!
          </mj-text>
          <mj-text color="#637381" font-size="16px">
            We're looking forward to meeting you.
          </mj-text>
        </mj-column>
      </mj-section>
      <mj-section background-color="#ffffff" padding-left="15px" padding-right="15px">
        <mj-column width="50%">
          <mj-text color="#212b35" font-size="12px" text-transform="uppercase" font-weight="bold" padding-bottom="0">
            address
          </mj-text>
          <mj-text color="#637381" font-size="14px" padding-top="0">
            Austin Convention Center
            <br />
            123 Main Street, 78701
          </mj-text>
        </mj-column>
        <mj-column width="50%">
          <mj-text color="#212b35" font-size="12px" text-transform="uppercase" font-weight="bold" padding-bottom="0">
            Hours of Operation
          </mj-text>
          <mj-text color="#637381" font-size="14px" padding-top="0">
            Monday, December 20th: 8:00AM - 5:00PM
            <br />
            Tuesday, December 21st: 8:00AM - 5:00PM
          </mj-text>
        </mj-column>
      </mj-section>
    </mj-wrapper>

    <mj-wrapper full-width="full-width">
      <mj-section>
        <mj-column width="100%" padding="0">
          <mj-social font-size="15px" icon-size="30px" mode="horizontal" padding="0" align="center">
            <mj-social-element name="facebook" href="https://mjml.io/" background-color="#A1A0A0">
            </mj-social-element>
            <mj-social-element name="google" href="https://mjml.io/" background-color="#A1A0A0">
            </mj-social-element>
            <mj-social-element name="twitter" href="https://mjml.io/" background-color="#A1A0A0">
            </mj-social-element>
            <mj-social-element name="linkedin" href="https://mjml.io/" background-color="#A1A0A0">
            </mj-social-element>
          </mj-social>
          <mj-text color="#445566" font-size="11px" font-weight="bold" align="center">
            View this email in your browser
          </mj-text>
          <mj-text color="#445566" font-size="11px" align="center" line-height="16px">
            You are receiving this email advertisement because you registered with my report. (123 Main Street, Austin, TX 78701) and agreed to receive emails from us regarding new features, events and special offers.
          </mj-text>
          <mj-text color="#445566" font-size="11px" align="center" line-height="16px">
            &copy; A Report Inc., All Rights Reserved.
          </mj-text>
        </mj-column>
      </mj-section>
      <mj-section padding-top="0">
        <mj-group>
          <mj-column width="100%" padding-right="0">
            <mj-text color="#445566" font-size="11px" align="center" line-height="16px" font-weight="bold">
              <a class="footer-link" href="https://www.google.com">Privacy</a>&#xA0;&#xA0;&#xA0;&#xA0;&#xA0;&#xA0;&#xA0;&#xA0;<a class="footer-link" href="https://www.google.com">Unsubscribe</a>
            </mj-text>
          </mj-column>
        </mj-group>

      </mj-section>
    </mj-wrapper>

  </mj-body>
</mjml>
"""

email_content = mjml2html(mjml_content)


load_dotenv()
gmail_address = os.environ["GMAIL_ADDRESS"]
gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
email_subject = "Report on the S&P 500 Built with MJML"

msg = MIMEMultipart("related")
msg["Subject"] = email_subject
msg["From"] = gmail_address
msg["To"] = gmail_address

msg_alt = MIMEMultipart("alternative")
msg.attach(msg_alt)
msg_alt.attach(MIMEText(email_content, "html"))

img = MIMEImage(plot1_bytes, _subtype="png")
img.add_header("Content-ID", "<plot1>")
msg.attach(img)

img = MIMEImage(plot2_bytes, _subtype="png")
img.add_header("Content-ID", "<plot2>")
msg.attach(img)

with open("examples/newspapers.jpg", "rb") as f:
    newspapers_bytes = f.read()
img = MIMEImage(newspapers_bytes, _subtype="jpeg")
img.add_header("Content-ID", "<newspapers>")
msg.attach(img)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(gmail_address, gmail_app_password)
    server.sendmail(msg["From"], [msg["To"]], msg.as_string())
