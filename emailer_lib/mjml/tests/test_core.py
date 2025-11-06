import pytest
from io import BytesIO
from emailer_lib.mjml._core import MJMLTag, TagAttrDict


def test_accepts_dict_arguments():
    attrs = TagAttrDict({"color": "red", "padding": "10px"})

    assert attrs["color"] == "red"
    assert attrs["padding"] == "10px"


def test_values_converted_to_strings():
    attrs = TagAttrDict({"width": 100, "visible": True, "opacity": 0.5})

    assert attrs["width"] == "100"
    assert attrs["visible"] == "True"
    assert attrs["opacity"] == "0.5"


def test_update_method():
    attrs = TagAttrDict({"color": "red"})
    attrs.update({"font-size": "14px", "padding": "10px"})

    assert attrs["color"] == "red"
    assert attrs["font-size"] == "14px"
    assert attrs["padding"] == "10px"


def test_tag_with_dict_attributes():
    attrs_dict = {"background-color": "#fff", "padding": "20px"}
    tag = MJMLTag("mj-section", attributes=attrs_dict)

    assert tag.attrs["background-color"] == "#fff"
    assert tag.attrs["padding"] == "20px"


def test_tag_filters_none_children():
    tag = MJMLTag("mj-column", MJMLTag("mj-text", content="Text"), None)
    mjml_content = tag._render_mjml()

    # None should not appear in output
    assert mjml_content.count("<mj-text>") == 1


def test_render_empty_tag():
    tag = MJMLTag("mj-spacer")
    mjml_content = tag._render_mjml()
    assert mjml_content == "<mj-spacer></mj-spacer>"


def test_render_with_attributes():
    tag = MJMLTag("mj-spacer", attributes={"height": "20px"})
    mjml_content = tag._render_mjml()
    assert mjml_content == '<mj-spacer height="20px"></mj-spacer>'


def test_render_with_custom_indent():
    tag = MJMLTag("mj-text", content="Hello")
    mjml_content = tag._render_mjml(indent=4)
    assert mjml_content.startswith("    <mj-text>")


def test_render_with_custom_eol():
    tag = MJMLTag("mj-text", content="Hello")
    mjml_content = tag._render_mjml(eol="\r\n")
    assert "\r\n" in mjml_content


def test_render_nested_tags():
    tag = MJMLTag(
        "mj-section", MJMLTag("mj-column", MJMLTag("mj-text", content="Nested"))
    )
    mjml_content = tag._render_mjml()

    assert "<mj-section>" in mjml_content
    assert "<mj-column>" in mjml_content
    assert "<mj-text>" in mjml_content
    assert "Nested" in mjml_content


def test_render_with_string_and_tag_children():
    child_tag = MJMLTag("mj-text", content="Tagged")
    tag = MJMLTag("mj-column", "Plain text", child_tag, "More text")
    mjml_content = tag._render_mjml()

    assert "Plain text" in mjml_content
    assert "<mj-text>" in mjml_content
    assert "More text" in mjml_content


def test_repr_returns_mjml():
    tag = MJMLTag("mj-text", content="Hello")

    assert repr(tag) == tag._render_mjml()


def test_to_html_with_complete_mjml_document():
    tag = MJMLTag("mjml", MJMLTag("mj-body", MJMLTag("mj-section")))
    html_result = tag.to_html()

    assert "<html" in html_result
    assert isinstance(html_result, str)


def test_to_html_warns_and_wraps_mj_body():
    tag = MJMLTag("mj-body", MJMLTag("mj-section"))

    with pytest.warns(UserWarning, match="Automatically wrapping in <mjml>"):
        html_result = tag.to_html()

    assert "html" in html_result


def test_to_html_warns_and_wraps_other_tags():
    tag = MJMLTag("mj-section", MJMLTag("mj-column"))

    with pytest.warns(UserWarning, match="Automatically wrapping in <mjml><mj-body>"):
        html_result = tag.to_html()

    assert "html" in html_result


def test_repr_html_calls_to_html():
    tag = MJMLTag("mjml", MJMLTag("mj-body"))
    html_from_repr = tag._repr_html_()
    html_from_method = tag.to_html()

    assert html_from_repr == html_from_method


def test_to_html_passes_kwargs_to_mjml2html():
    tag = MJMLTag("mjml", MJMLTag("mj-body"))
    result = tag.to_html(social_icon_origin="https://www.example.com")

    assert "html" in result


def test_leaf_tag_raises_on_children():
    with pytest.raises(TypeError, match="is a leaf tag and accepts only one positional argument"):
        MJMLTag("mj-text", "content", MJMLTag("mj-column"), _is_leaf=True)


def test_leaf_tag_content_type_validation():
    with pytest.raises(TypeError, match="content must be a string, int, or float"):
        MJMLTag("mj-text", content=["invalid", "list"], _is_leaf=True)


def test_leaf_tag_attributes_type_validation():
    with pytest.raises(TypeError, match="attributes must be a dict or TagAttrDict"):
        MJMLTag("mj-text", "content", attributes="invalid", _is_leaf=True)

def test_container_tag_attributes_type_validation():
    with pytest.raises(TypeError, match="attributes must be a dict or TagAttrDict.*use positional arguments for container tags"):
        MJMLTag("mj-section", attributes="invalid")

def test_children_sequence_flattening():
    child1 = MJMLTag("mj-text", content="Text 1")
    child2 = MJMLTag("mj-text", content="Text 2")
    child3 = MJMLTag("mj-text", content="Text 3")

    tag = MJMLTag("mj-column", [child1, child2], child3)

    assert len(tag.children) == 3
    assert tag.children[0] == child1
    assert tag.children[1] == child2
    assert tag.children[2] == child3

    mjml_content = tag._render_mjml()
    
    assert mjml_content.count("<mj-text>") == 3
    assert "Text 1" in mjml_content
    assert "Text 2" in mjml_content
    assert "Text 3" in mjml_content


def test_render_mjml_raises_on_bytesio_in_image_src():
    image_data = BytesIO(b"fake image data")
    image_tag = MJMLTag(
        "mj-image",
        attributes={"src": image_data, "alt": "Test"}
    )
    
    with pytest.raises(ValueError, match="Cannot render MJML with BytesIO/bytes"):
        image_tag._render_mjml()


def test_render_mjml_raises_on_bytes_in_image_src():
    image_data = b"fake image data"
    image_tag = MJMLTag(
        "mj-image",
        attributes={"src": image_data, "alt": "Test"}
    )
    
    with pytest.raises(ValueError, match="Cannot render MJML with BytesIO/bytes"):
        image_tag._render_mjml()


def test_tagattr_dict_stores_bytesio():
    """Test that TagAttrDict can store BytesIO values."""
    image_data = BytesIO(b"test data")
    attrs = TagAttrDict({"src": image_data, "alt": "Test"})
    
    # Verify BytesIO is stored as-is
    assert isinstance(attrs["src"], BytesIO)
    assert attrs["alt"] == "Test"


def test_tagattr_dict_stores_bytes():
    """Test that TagAttrDict can store bytes values."""
    image_data = b"test data"
    attrs = TagAttrDict({"src": image_data, "alt": "Test"})
    
    # Verify bytes are stored as-is
    assert isinstance(attrs["src"], bytes)
    assert attrs["alt"] == "Test"
