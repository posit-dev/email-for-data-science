"""
Image preprocessing for MJML tags.

This module handles conversion of image bytes to CID-referenced inline 
attachments for email embedding without using globals.
"""

from __future__ import annotations
from typing import Any, Dict, Tuple
import base64
import uuid
from io import BytesIO

from ._core import MJMLTag

__all__ = []


def _convert_to_bytes(obj: Any) -> bytes:
    """
    Convert bytes or BytesIO to bytes.
    
    Parameters
    ----------
    obj
        The object to convert (bytes or BytesIO)
        
    Returns
    -------
    bytes
        The binary representation of the object
        
    Raises
    ------
    TypeError
        If the object type is not supported
    """
    if isinstance(obj, BytesIO):
        return obj.getvalue()
    
    if isinstance(obj, bytes):
        return obj
    
    raise TypeError(
        f"Unsupported image type: {type(obj).__name__}. "
        "Expected bytes or BytesIO."
    )


def _process_mjml_images(mjml_tag: MJMLTag) -> Tuple[MJMLTag, Dict[str, str]]:
    """
    Extract inline attachments from MJML tree and convert bytes/BytesIO to CID references.
    
    This is a private function. Users should not call it directly.
    It is called automatically by mjml_to_email().
    
    This function recursively walks through the MJML tag tree and finds mj-image tags
    with BytesIO or bytes in their src attribute. It converts these to CID references
    and extracts the base64 data for the inline_attachments dictionary.
    
    Parameters
    ----------
    mjml_tag
        The MJML tag tree to process
        
    Returns
    -------
    Tuple[MJMLTag, Dict[str, str]]
        A tuple of:\n
        - The modified MJML tag tree with BytesIO/bytes converted to CID references
        - Dictionary mapping CID filenames to base64-encoded image data
        
    Examples
    --------
    ```{python}
    from nbmail.mjml import mjml, body, section, column, image, text
    from nbmail import mjml_to_email
    from io import BytesIO
    import numpy as np
    import pandas as pd
    from plotnine import ggplot, aes, geom_boxplot

    # Create the plot data
    variety = np.repeat(["A", "B", "C", "D", "E", "F", "G"], 40)
    treatment = np.tile(np.repeat(["high", "low"], 20), 7)
    note = np.arange(1, 281) + np.random.choice(np.arange(1, 151), 280, replace=True)
    data = pd.DataFrame({"variety": variety, "treatment": treatment, "note": note})

    # Create the plot
    gg = ggplot(data, aes(x="variety", y="note", fill="treatment")) + geom_boxplot()

    # Save plot to BytesIO buffer
    buf = BytesIO()
    gg.save(buf, format='png', dpi=100, verbose=False)
    buf.seek(0)

    email = mjml(
        body(
            section(
                column(
                    text("A plot from plotnine in an email")
                ),
                column(
                    image(attributes={
                        "src": buf,
                        "alt": "My Plot",
                        "width": "600px"
                    })
                )
            )
        )
    )

    mjml_to_email(email)
    ```
    """
    inline_attachments: Dict[str, str] = {}
    
    def _process_tag(tag: MJMLTag) -> MJMLTag:
        """Recursively process a tag and its children."""
        
        # Handle mj-image tags with BytesIO/bytes in src attribute
        if tag.tagName == "mj-image" and "src" in tag.attrs:
            src_value = tag.attrs["src"]
            
            # Check if src is BytesIO or bytes
            if isinstance(src_value, (bytes, BytesIO)):
                # Convert to bytes and encode to base64
                image_bytes_data = _convert_to_bytes(src_value)
                b64_string = base64.b64encode(image_bytes_data).decode("utf-8")
                
                # Generate CID filename using UUID
                cid_id = uuid.uuid4().hex[:8]
                cid_filename = f"plot_{cid_id}.png"
                
                # Store in attachments
                inline_attachments[cid_filename] = b64_string
                
                # Create new tag with CID reference instead of BytesIO
                new_attrs = dict(tag.attrs)
                new_attrs["src"] = f"cid:{cid_filename}"
                new_tag = MJMLTag(
                    tag.tagName,
                    attributes=new_attrs,
                    content=tag.content,
                    _is_leaf=tag._is_leaf
                )
                
                # Process children
                for child in tag.children:
                    if isinstance(child, MJMLTag):
                        new_tag.children.append(_process_tag(child))
                    else:
                        new_tag.children.append(child)
                
                return new_tag
        
        # For all other tags, process recursively
        new_tag = MJMLTag(
            tag.tagName,
            attributes=dict(tag.attrs),
            content=tag.content,
            _is_leaf=tag._is_leaf
        )
        
        for child in tag.children:
            if isinstance(child, MJMLTag):
                new_tag.children.append(_process_tag(child))
            else:
                new_tag.children.append(child)
        
        return new_tag
    
    # Process the entire tag tree
    processed_tag = _process_tag(mjml_tag)
    
    return processed_tag, inline_attachments
