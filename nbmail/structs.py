from __future__ import annotations
from dataclasses import dataclass, field
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import re
import json

from email.message import EmailMessage
import tempfile
import webbrowser

from .utils import _add_base_64_to_inline_attachments

__all__ = ["Email"]


@dataclass
class Email:
    """
    A serializable, previewable, sendable email object for data science workflows.

    The `Email` class provides a unified structure for representing email messages,
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

    email_suppress_report_attachment
        Whether to suppress report attachments (used in some workflows).

    email_suppress_scheduled
        Whether to suppress scheduled sending (used in some workflows).

    Examples
    --------
    ```python
    email = Email(
        html="<p>Hello world</p>",
        subject="Test Email",
        recipients=["user@example.com"],
    )
    email.write_preview_email("preview.html")
    ```
    """

    html: str
    subject: str
    email_suppress_report_attachment: bool | None = None
    email_suppress_scheduled: bool | None = None

    # is a list of files in path from current directory
    external_attachments: list[str] = field(default_factory=list)

    # has structure {filename: base64_string}
    inline_attachments: dict[str, str] = field(default_factory=dict)

    text: str | None = None  # sometimes present in quarto
    recipients: list[str] | None = None  # not present in quarto

    def _generate_preview_html(self) -> str:
        """
        Generate preview HTML with inline attachments embedded as base64 data URIs.

        This internal method converts `cid:` references in the HTML to base64 data URIs,
        making the HTML self-contained for preview purposes. This is distinct from the
        HTML used in egress.py where cid references are kept and images are attached
        as separate MIME parts.

        Returns
        -------
        str
            HTML content with inline attachments embedded as base64 data URIs.
        """
        html_with_inline = re.sub(
            r'src="cid:([^"\s]+)"',
            _add_base_64_to_inline_attachments(self.inline_attachments),
            self.html,
        )
        return html_with_inline

    def _add_subject_header(self, html: str) -> str:
        """
        Add subject line as a header in the HTML.

        Parameters
        ----------
        html
            The HTML content to add the subject to

        Returns
        -------
        str
            HTML with subject header added
        """
        if self.subject:
            subject_ln = (
                "<br><br><strong><span style=\"font-variant: small-caps;\">"
                "email subject: </span></strong>"
                f"{re.escape(self.subject)}"
                "<br>"
            )
        else:
            subject_ln = ""

        if "<body" in html:
            html = re.sub(
                r"(<body[^>]*>)",
                r'\1' + subject_ln,
                html,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            # Fallback: prepend if no <body> tag found
            html = subject_ln + html

        return html

    def _repr_html_(self) -> str:
        """
        Return HTML representation with inline attachments for rich display.

        This method enables rich display of the Email in Jupyter notebooks
        and other IPython-compatible environments. It converts cid: references to
        base64 data URIs so the email can be previewed directly in the notebook.

        Returns
        -------
        str
            HTML content with inline attachments embedded as base64 data URIs.

        Examples
        --------
        ```python
        # In a Jupyter notebook, simply display the email object:
        email = Email(
            html='<p>Hello <img src="cid:img1.png"/></p>',
            subject="Test Email",
            inline_attachments={"img1.png": "iVBORw0KGgo..."}
        )
        email  # This will automatically call _repr_html_() for rich display
        ```
        """
        html_with_inline = self._generate_preview_html()
        return self._add_subject_header(html_with_inline)

    def write_preview_email(self, out_file: str = "preview_email.html") -> None:
        """
        Write a preview HTML file with inline attachments embedded.

        This method replaces image sources in the HTML with base64-encoded data from
        inline attachments, allowing you to preview the email as it would appear to recipients.
        The generated HTML is self-contained with base64 data URIs, distinct from the email
        sent via egress.py which uses cid references with MIME attachments.

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
        # Generate the preview HTML with inline base64 images
        html_with_inline = self._generate_preview_html()
        # Add subject header
        html_with_inline = self._add_subject_header(html_with_inline)

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html_with_inline)

        if self.external_attachments:
            raise ValueError("Preview does not yet support external attachments.")

    def write_email_message(self) -> EmailMessage:
        """
        Convert the Email to a Python EmailMessage.

        This method creates a standard library EmailMessage object from the
        Email, including HTML, plain text, recipients, and attachments.

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

    def show_browser(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            f_path = Path(tmp_dir) / "index.html"

            # Generate the preview HTML with inline base64 images
            html_with_inline = self._generate_preview_html()
            html_with_inline = self._add_subject_header(html_with_inline)
            f_path.write_text(html_with_inline, encoding="utf-8")

            # create a server that closes after 1 request ----
            server = _create_temp_file_server(f_path)
            webbrowser.open(f"http://127.0.0.1:{server.server_port}/{f_path.name}")
            server.handle_request()

    def preview_send_email(self):
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

    def write_quarto_json(self, out_file: str = ".output_metadata.json") -> None:
        """
        Write the Email to Quarto's output metadata JSON format.

        This method serializes the Email object to JSON in the format expected by Quarto,
        making it compatible with Quarto's email integration workflows. This is the inverse
        of the `quarto_json_to_email()` ingress function.

        Parameters
        ----------
        out_file
            The file path to write the Quarto metadata JSON. Defaults to ".output_metadata.json".

        Returns
        -------
        None

        Examples
        --------
        ```python
        email = Email(
            html="<p>Hello world</p>",
            subject="Test Email",
        )
        email.write_quarto_json("email_metadata.json")
        ```

        Notes
        ------
        The output JSON includes:\n
        - email_subject: The subject line
        - email_attachments: List of attachment file paths
        - email_body_html: The HTML content of the email
        - email_body_text: Plain text version (if present)
        - email_images: Dictionary of base64-encoded inline images (only if not empty)
        - email_suppress_report_attachment: Suppression flag for report attachments
        - email_suppress_scheduled: Suppression flag for scheduled sending
        """
        metadata = {
            "email_subject": self.subject,
            "email_attachments": self.external_attachments or [],
            "email_body_html": self.html,
        }

        # Add optional text field if present
        if self.text:
            metadata["email_body_text"] = self.text

        # Add inline images only if not empty
        if self.inline_attachments:
            metadata["email_images"] = self.inline_attachments

        # Add suppression flags if they are set (not None)
        if self.email_suppress_report_attachment is not None:
            metadata["email_suppress_report_attachment"] = (
                self.email_suppress_report_attachment
            )

        if self.email_suppress_scheduled is not None:
            metadata["email_suppress_scheduled"] = self.email_suppress_scheduled

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)


#### Helpers ####


## To help mimic Great Tables method: GT.show(target="browser")
class PatchedHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Patched handler, which does not log requests to stderr"""


def _create_temp_file_server(fname: Path) -> HTTPServer:
    """Return a HTTPServer, so we can serve a single request (to show the table)."""

    Handler = partial(PatchedHTTPRequestHandler, directory=str(fname.parent))
    server = HTTPServer(("127.0.0.1", 0), Handler)

    return server
