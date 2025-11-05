"""
Image preprocessing for MJML tags.

This module handles conversion of image bytes to CID-referenced inline 
attachments for email embedding without using globals.
"""

from __future__ import annotations
from typing import Any, Dict, Tuple
import base64
from io import BytesIO

from ._core import MJMLTag

__all__ = ["process_mjml_images"]

# Counter for generating sequential CID filenames
_cid_counter = [0]


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


def process_mjml_images(mjml_tag: MJMLTag) -> Tuple[MJMLTag, Dict[str, str]]:
    """
    Extract inline attachments from MJML tree and convert bytes/BytesIO to CID references.
    
    This function recursively walks through the MJML tag tree and finds mj-image tags
    with BytesIO or bytes in their src attribute. It converts these to CID references
    and extracts the base64 data for the inline_attachments dictionary.
    
    Note: This function should be called before render_mjml(). If render_mjml() is called
    on a tag with BytesIO/bytes, it will raise an error directing you to use this approach.
    
    Parameters
    ----------
    mjml_tag
        The MJML tag tree to process
        
    Returns
    -------
    Tuple[MJMLTag, Dict[str, str]]
        A tuple of:
        - The modified MJML tag tree with BytesIO/bytes converted to CID references
        - Dictionary mapping CID filenames to base64-encoded image data
        
    Examples
    --------
    ```python
    from emailer_lib.mjml import mjml, body, section, column, image
    from emailer_lib import mjml_to_intermediate_email
    from io import BytesIO
    
    # Create BytesIO with image data
    buf = BytesIO(b'...png binary data...')
    
    # Create MJML using regular image() with BytesIO as src
    email = mjml(
        body(
            section(
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
    
    # Pass directly to mjml_to_intermediate_email (calls process_mjml_images internally)
    i_email = mjml_to_intermediate_email(email)
    
    # Result: i_email.inline_attachments = {"plot_1.png": "iVBORw0KGgo..."}
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
                
                # Generate CID filename
                _cid_counter[0] += 1
                cid_filename = f"plot_{_cid_counter[0]}.png"
                
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
