from methods import send_quarto_email_with_gmail, write_email_message_to_file, _read_quarto_email_json
import os
from dotenv import load_dotenv

from great_tables import GT
import os
from plotnine import ggplot, aes, geom_point, labs
import pandas as pd
import base64
from io import BytesIO

load_dotenv()

password = os.environ["POSIT_APP_PASSWORD"]
username = os.environ["POSIT_ADDRESS"]

# send_quarto_email_with_gmail(
#     username=username,
#     password=password,
#     json_path=".output_metadata.json",
#     recipients=[username]
# )




# Simple text
body_text = "<p>Hello, this is a test email with text, a plot, an image, and a table.</p>"

# Simple plot with plotnine
df = pd.DataFrame({'x': [1, 2, 3], 'y': [3, 2, 1]})
p = ggplot(df, aes('x', 'y')) + geom_point() + labs(title="A Simple Plot")

buf = BytesIO()
p.save(buf, format='png')
buf.seek(0)
plot_bytes = buf.read()

plot_html = '<img src="cid:plot-image" alt="plotnine plot"/><br>'

# Simple image (embed as base64)
image_path = "../examples/newspapers.jpg"


with open(image_path, "rb") as img_file:
    image_bytes = img_file.read()

image_html = '<img src="cid:photo-image" alt="placeholder image"/><br>'

image_html

# Simple table with GT
table_df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
gt = GT(table_df)
table_html = gt.as_raw_html()

result_head = """
<meta charset="utf-8">
<title>Email Preview</title>
"""

# Wrap the email body in the HTML structure

# Modified for redmail, but there are certainly other ways to do this without the ugly jinja syntax in python
email_body = f"""<!doctype html>
<html>
  <head>
{result_head}
  </head>
  <body>
{body_text} {{{{ plot_image }}}}  {{{{ photo_image }}}} {table_html}
  </body>
</html>"""

from dotenv import load_dotenv
load_dotenv()

from redmail import gmail

password = os.environ["GMAIL_APP_PASSWORD"]
username = os.environ["GMAIL_ADDRESS"]

gmail.username = username
gmail.password = password


msg = gmail.get_message(
    subject="An example email",
    receivers=[username],
    body_images={
      'plot_image': plot_bytes,
      'photo_image': image_path,
    },
    html=email_body,
)


write_email_message_to_file(msg)

# struct = _read_quarto_email_json(".output_metadata.json")
# struct.write_preview_email("struct_preview.html")


