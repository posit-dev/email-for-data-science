from __future__ import annotations
from dataclasses import dataclass
import re

from email.message import EmailMessage

from .utils import _add_base_64_to_inline_attachments

__all__ = ["IntermediateEmail"]


@dataclass
class IntermediateEmail:
    html: str
    subject: str
    rsc_email_supress_report_attachment: bool
    rsc_email_supress_scheduled: bool

    # is a list of files in path from current directory
    external_attachments: list[str] | None = None

    # has structure {filename: base64_string}
    inline_attachments: dict[str, str] | None = None

    text: str | None = None  # sometimes present in quarto
    recipients: list[str] | None = None  # not present in quarto

    def write_preview_email(self, out_file: str = "preview_email.html") -> None:
        html_with_inline = re.sub(
            r'src="cid:([^"\s]+)"',
            _add_base_64_to_inline_attachments(self.inline_attachments),
            self.html,
        )

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html_with_inline)

        if self.external_attachments:
            raise ValueError("Preview does not yet support external attachments.")

    def write_email_message(self) -> EmailMessage:
        pass

    # sends just to some preview recipient?
    def preview_send_email():
        pass
