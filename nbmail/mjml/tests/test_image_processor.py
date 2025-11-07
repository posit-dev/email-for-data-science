import pytest
from io import BytesIO

from nbmail.mjml.image_processor import _convert_to_bytes, _process_mjml_images
from nbmail.mjml._core import MJMLTag


def test_convert_to_bytes_from_bytesio():
    data = b"test image data"
    bytesio_obj = BytesIO(data)
    
    result = _convert_to_bytes(bytesio_obj)
    
    assert isinstance(result, bytes)
    assert result == data


def test_convert_to_bytes_from_bytes():
    data = b"test image data"
    
    result = _convert_to_bytes(data)
    
    assert isinstance(result, bytes)
    assert result == data


def test_convert_to_bytes_raises_on_invalid_type():
    with pytest.raises(TypeError, match="Unsupported image type"):
        _convert_to_bytes("string")
    
    with pytest.raises(TypeError, match="Unsupported image type"):
        _convert_to_bytes(123)
    
    with pytest.raises(TypeError, match="Unsupported image type"):
        _convert_to_bytes([b"data"])


def test_process_mjml_images_with_bytesio():
    image_data = b"fake png data"
    bytesio_obj = BytesIO(image_data)
    
    # Create MJML tag with BytesIO image
    image_tag = MJMLTag(
        "mj-image",
        attributes={"src": bytesio_obj, "alt": "Test"}
    )
    
    processed_tag, inline_attachments = _process_mjml_images(image_tag)
    
    assert len(inline_attachments) == 1
    
    cid_filename = list(inline_attachments.keys())[0]
    assert cid_filename.startswith("plot_") and cid_filename.endswith(".png")
    assert processed_tag.attrs["src"] == f"cid:{cid_filename}"
    assert isinstance(inline_attachments[cid_filename], str)
    assert len(inline_attachments[cid_filename]) > 0


def test_process_mjml_images_with_bytes():
    image_data = b"fake png data"
    
    # Create MJML tag with bytes image
    image_tag = MJMLTag(
        "mj-image",
        attributes={"src": image_data, "alt": "Test"}
    )
    
    processed_tag, inline_attachments = _process_mjml_images(image_tag)
    
    assert len(inline_attachments) == 1
    
    cid_filename = list(inline_attachments.keys())[0]
    assert cid_filename.startswith("plot_") and cid_filename.endswith(".png")
    assert processed_tag.attrs["src"] == f"cid:{cid_filename}"
    assert isinstance(inline_attachments[cid_filename], str)
    assert len(inline_attachments[cid_filename]) > 0


def test_process_mjml_images_multiple_images():
    image_data_1 = b"fake png data 1"
    image_data_2 = b"fake png data 2"
    
    # Create MJML structure with multiple images
    col = MJMLTag(
        "mj-column",
        MJMLTag("mj-image", attributes={"src": BytesIO(image_data_1), "alt": "Img1"}),
        MJMLTag("mj-image", attributes={"src": BytesIO(image_data_2), "alt": "Img2"}),
    )
    
    processed_tag, inline_attachments = _process_mjml_images(col)
    
    assert len(inline_attachments) == 2
    
    cid_filenames = list(inline_attachments.keys())
    assert all(f.startswith("plot_") and f.endswith(".png") for f in cid_filenames)
    assert cid_filenames[0] != cid_filenames[1]
    
    children_with_images = [c for c in processed_tag.children if isinstance(c, MJMLTag)]
    assert children_with_images[0].attrs["src"] == f"cid:{cid_filenames[0]}"
    assert children_with_images[1].attrs["src"] == f"cid:{cid_filenames[1]}"


def test_process_mjml_images_preserves_other_attributes():
    image_data = b"fake png data"
    
    image_tag = MJMLTag(
        "mj-image",
        attributes={
            "src": BytesIO(image_data),
            "alt": "Test Image",
            "width": "600px",
            "padding": "10px"
        }
    )
    
    processed_tag, _ = _process_mjml_images(image_tag)
    
    assert processed_tag.attrs["alt"] == "Test Image"
    assert processed_tag.attrs["width"] == "600px"
    assert processed_tag.attrs["padding"] == "10px"


def test_process_mjml_images_preserves_non_image_tags():
    # Create MJML structure with mixed content
    section = MJMLTag(
        "mj-section",
        MJMLTag("mj-column",
            MJMLTag("mj-text", content="Hello"),
            MJMLTag("mj-image", attributes={"src": BytesIO(b"data"), "alt": "Img"}),
            MJMLTag("mj-text", content="World"),
        )
    )
    
    processed_tag, inline_attachments = _process_mjml_images(section)
    
    assert processed_tag.tagName == "mj-section"
    column = processed_tag.children[0]
    assert column.tagName == "mj-column"
    assert len(column.children) == 3
    
    assert column.children[0].tagName == "mj-text"
    assert column.children[0].content == "Hello"
    assert column.children[2].tagName == "mj-text"
    assert column.children[2].content == "World"
    
    assert column.children[1].tagName == "mj-image"
    cid_filename = list(inline_attachments.keys())[0]
    assert column.children[1].attrs["src"] == f"cid:{cid_filename}"
