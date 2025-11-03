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

__all__ = ["process_mjml_images", "image_bytes"]

# Counter for generating sequential CID filenames
_cid_counter = [0]


def image_bytes(*args, attributes=None, content=None):
    """
    Create an MJML image tag from bytes or BytesIO.
    
    This function pre-processes BytesIO/bytes into mj-raw tags containing
    HTML img elements with CID references. The base64 data and CID filename
    are stored as tag attributes for extraction by process_mjml_images().
    
    Parameters
    ----------
    *args
        Children (MJMLTag objects)
    attributes
        Optional dict of tag attributes (alt, width, etc.)
    content
        Optional text content for the tag
    
    Returns
    -------
    MJMLTag
        mj-raw tag with HTML img using actual CID reference (e.g., cid:plot_1.png)
    """
    from .tags import image as original_image
    
    # If no attributes or no src, use regular image tag
    if not attributes or "src" not in attributes:
        return original_image(*args, attributes=attributes, content=content)
    
    src_value = attributes["src"]
    
    # If src is bytes or BytesIO, process immediately
    if isinstance(src_value, (bytes, BytesIO)):
        image_bytes_data = _convert_to_bytes(src_value)
        b64_string = base64.b64encode(image_bytes_data).decode("utf-8")
        
        # Generate CID filename immediately (for use in repr)
        _cid_counter[0] += 1
        cid_filename = f"plot_{_cid_counter[0]}.png"
        
        # Create HTML img tag with actual CID reference
        width = attributes.get("width", "100%")
        alt = attributes.get("alt", "Image")
        html_content = f'<img src="cid:{cid_filename}" alt="{alt}" width="{width}" style="max-width: 100%; height: auto;" />'
        
        # Return mj-raw tag with both CID filename and base64 data in attributes
        tag_attrs = {
            "_cid_filename": cid_filename,
            "_cid_data": b64_string
        }
        return MJMLTag("mj-raw", content=html_content, attributes=tag_attrs, _is_leaf=True)
    
    # If src is a string (URL), use regular image tag
    return original_image(*args, attributes=attributes, content=content)


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
    Extract inline attachments from MJML tree.
    
    This function recursively walks through the MJML tag tree and finds
    mj-raw tags that have _cid_data and _cid_filename attributes (created 
    by image_bytes()). It extracts the base64 data and builds the attachments
    dictionary. The HTML img tags already have correct cid: references from
    when image_bytes() created them.
    
    Parameters
    ----------
    mjml_tag
        The MJML tag tree to process
        
    Returns
    -------
    Tuple[MJMLTag, Dict[str, str]]
        A tuple of:
        - The modified MJML tag tree with special attributes removed
        - Dictionary mapping CID filenames to base64-encoded image data
        
    Examples
    --------
    ```python
    from emailer_lib.mjml import mjml, body, section, column
    from emailer_lib.mjml.image_processor import image_bytes, process_mjml_images
    from io import BytesIO
    
    # Create BytesIO with image data
    buf = BytesIO(b'...png binary data...')
    
    # Create MJML using image_bytes() - stores CID and data in tag attributes
    email = mjml(
        body(
            section(
                column(
                    image_bytes(attributes={
                        "src": buf,
                        "alt": "My Plot",
                        "width": "600px"
                    })
                )
            )
        )
    )
    
    # Process to extract attachments
    processed_email, attachments = process_mjml_images(email)
    
    # Result: 
    # - processed_email has img src already set to cid:plot_1.png
    # - attachments = {"plot_1.png": "iVBORw0KGgo..."}
    ```
    """
    inline_attachments: Dict[str, str] = {}
    
    def _process_tag(tag: MJMLTag) -> MJMLTag:
        """Recursively process a tag and its children."""
        
        # Handle mj-raw tags with _cid_data attribute (from image_bytes)
        if tag.tagName == "mj-raw" and "_cid_data" in tag.attrs:
            # Extract the CID filename and base64 data
            cid_filename = tag.attrs.get("_cid_filename", "image.png")
            b64_string = tag.attrs["_cid_data"]
            
            # Store in attachments
            inline_attachments[cid_filename] = b64_string
            
            # Create new tag without the special attributes
            new_tag = MJMLTag(tag.tagName, content=tag.content, _is_leaf=tag._is_leaf)
            # Copy other attributes except _cid_data and _cid_filename
            for k, v in tag.attrs.items():
                if k not in ("_cid_data", "_cid_filename"):
                    new_tag.attrs[k] = v
            
            return new_tag
        
        # For all other tags, process recursively
        new_tag = MJMLTag(tag.tagName, attributes=dict(tag.attrs), content=tag.content, _is_leaf=tag._is_leaf)
        
        for child in tag.children:
            if isinstance(child, MJMLTag):
                new_tag.children.append(_process_tag(child))
            else:
                new_tag.children.append(child)
        
        return new_tag
    
    # Process the entire tag tree
    processed_tag = _process_tag(mjml_tag)
    
    return processed_tag, inline_attachments
