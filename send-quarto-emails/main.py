from methods import send_quarto_email_with_gmail
import os
from dotenv import load_dotenv

os.chdir(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

password = os.environ["GMAIL_APP_PASSWORD"]
username = os.environ["GMAIL_ADDRESS"]

send_quarto_email_with_gmail(
    username=username,
    password=password,
    json_path=".output_metadata.json",
    recipients=[username, "jules.walzergoldfeld@posit.co"]
)
