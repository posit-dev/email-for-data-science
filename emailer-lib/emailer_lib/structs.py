from __future__ import annotations
from dataclasses import dataclass
import re

from email.message import EmailMessage

from .utils import _add_base_64_to_inline_attachments

__all__ = ["IntermediateEmail"]


@dataclass
class IntermediateEmail:
    """
    A serializable, previewable, sendable email object for data science workflows.

    The `IntermediateEmail` class provides a unified structure for representing email messages,
    including HTML and plain text content, subject, inline or external attachments, and recipients.
    It is designed to be generated from a variety of authoring tools and sent via multiple providers.

    Parameters
    ----------
    html
        The HTML content of the email.

    subject
        The subject line of the email.

    external_attachments
        List of file paths for external attachments to include.

    inline_attachments
        Dictionary mapping filenames to base64-encoded strings for inline attachments.

    text
        Optional plain text version of the email.

    recipients
        Optional list of recipient email addresses.

    rsc_email_supress_report_attachment
        Whether to suppress report attachments (used in some workflows).

    rsc_email_supress_scheduled
        Whether to suppress scheduled sending (used in some workflows).

    Examples
    --------
    ```python
    email = IntermediateEmail(
        html="<p>Hello world</p>",
        subject="Test Email",
        recipients=["user@example.com"],
    )
    email.write_preview_email("preview.html")
    ```
    """

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
        """
        Write a preview HTML file with inline attachments embedded.

        This method replaces image sources in the HTML with base64-encoded data from
        inline attachments, allowing you to preview the email as it would appear to recipients.

        Parameters
        ----------
        out_file
            The file path to write the preview HTML. Defaults to "preview_email.html".

        Returns
        -------
        None

        Examples
        --------
        ```python
        email.write_preview_email("preview.html")
        ```

        Notes
        ------
        Raises ValueError if external attachments are present, as preview does not support them.
        """
        html_with_inline = re.sub(
            r'src="cid:([^"\s]+)"',
            _add_base_64_to_inline_attachments(self.inline_attachments),
            self.html,
        )

        # Insert subject as <h2> after the opening <body> tag, if present
        if "<body" in html_with_inline:
            html_with_inline = re.sub(
                r"(<body[^>]*>)",
                r'\1\n<h2 style="padding-left:16px;">Subject: {}</h2>'.format(self.subject),
                html_with_inline,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            # Fallback: prepend if no <body> tag found
            html_with_inline = f'<h2 style="padding-left:16px;">Subject: {self.subject}</h2>\n' + html_with_inline

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html_with_inline)

        if self.external_attachments:
            raise ValueError("Preview does not yet support external attachments.")

    def write_email_message(self) -> EmailMessage:
        """
        Convert the IntermediateEmail to a Python EmailMessage.

        This method creates a standard library EmailMessage object from the
        IntermediateEmail, including HTML, plain text, recipients, and attachments.

        Returns
        -------
        EmailMessage
            The constructed EmailMessage object.

        Examples
        --------
        ```python
        msg = email.write_email_message()
        ```
        """
        raise NotImplementedError

    def preview_send_email():
        """
        Send a preview of the email to a test recipient.

        This method is intended for sending the email to a designated preview recipient
        for testing purposes before sending to the full recipient list.

        Returns
        -------
        None

        Examples
        --------
        ```python
        email.preview_send_email()
        ```
        """
        raise NotImplementedError
