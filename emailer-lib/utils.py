from __future__ import annotations
import base64
from email.message import EmailMessage
import re


# TODO: make sure this is not losing other attributes of the inline attachments
def _add_base_64_to_inline_attachments(inline_attachments: dict[str, str]):
    # Replace all src="cid:..." in the HTML
    def replace_cid(match):
        cid = match.group(1)
        img_data = inline_attachments.get(cid)
        if img_data:
            # TODO: this is kinda hacky
            # If it's a string, decode from base64 to bytes first
            if isinstance(img_data, str):
                try:
                    img_bytes = base64.b64decode(img_data)
                except Exception:
                    # If not base64, treat as raw bytes
                    img_bytes = img_data.encode("utf-8")
            else:
                img_bytes = img_data
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            return f'src="data:image;base64,{b64}"'
        return match.group(0)

    return replace_cid


def write_email_message_to_file(
    msg: EmailMessage, out_file: str = "preview_email.html"
):
    """
    Writes the HTML content of an email message to a file, inlining any images referenced by Content-ID (cid).

    This function extracts all attachments referenced by Content-ID from the given EmailMessage,
    replaces any `src="cid:..."` references in the HTML body with base64-encoded image data,
    and writes the resulting HTML to the specified output file.

    Params:
        msg (EmailMessage): The email message object containing the HTML body and attachments.
        out_file (str, optional): The path to the output HTML file. Defaults to "preview_email.html".

    Returns:
        None
    """
    inline_attachments = {}

    for part in msg.walk():
        content_id = part.get("Content-ID")
        if content_id:
            cid = content_id.strip("<>")

            payload = part.get_payload(decode=True)
            inline_attachments[cid] = payload

    html = msg.get_body(preferencelist=("html")).get_content()

    # Replace each cid reference with base64 data
    html_inline = re.sub(
        r'src="cid:([^"]+)"',
        _add_base_64_to_inline_attachments(inline_attachments),
        html,
    )

    # Write to file
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_inline)
