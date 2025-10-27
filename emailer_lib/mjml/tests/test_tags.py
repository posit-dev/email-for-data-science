import pytest
from emailer_lib.mjml import (
    MJMLTag,
    mjml,
    head,
    body,
    section,
    column,
    text,
    button,
    image,
    raw,
    accordion,
    accordion_element,
    accordion_text,
    accordion_title,
    navbar,
    navbar_link,
    social,
    social_element,
    carousel,
    carousel_image,
    table,
    mj_attributes,
    mj_all,
    mj_class,
)


def test_container_tag_accepts_children():
    sec = section(
        column(
            text(content="Hello")
        )
    )

    assert isinstance(sec, MJMLTag)
    assert sec.tagName == "mj-section"
    assert len(sec.children) == 1
    assert sec.children[0].tagName == "mj-column"
    
    mjml_content = sec.render_mjml()
    assert "<mj-section>" in mjml_content
    assert "<mj-column>" in mjml_content
    assert "<mj-text>" in mjml_content
    assert "Hello" in mjml_content
    assert "</mj-section>" in mjml_content


def test_container_tag_accepts_attributes():
    sec = section(attributes={"background-color": "#fff", "padding": "20px"})

    assert sec.attrs["background-color"] == "#fff"
    assert sec.attrs["padding"] == "20px"
    
    mjml_content = sec.render_mjml()
    assert '<mj-section background-color="#fff" padding="20px">' in mjml_content


def test_container_tag_accepts_children_and_attrs():
    sec = section(
        column(text(content="Col 1")),
        column(text(content="Col 2")),
        attributes={"background-color": "#f0f0f0"}
    )
    assert len(sec.children) == 2
    assert sec.attrs["background-color"] == "#f0f0f0"
    
    mjml_content = sec.render_mjml()
    assert 'background-color="#f0f0f0"' in mjml_content
    assert "Col 1" in mjml_content
    assert "Col 2" in mjml_content


def test_leaf_tag_accepts_content():
    txt = text(content="Hello World")

    assert isinstance(txt, MJMLTag)
    assert txt.tagName == "mj-text"
    assert txt.content == "Hello World"
    
    mjml_content = txt.render_mjml()
    assert mjml_content == "<mj-text>\nHello World\n</mj-text>"


def test_leaf_tag_accepts_attributes():
    txt = text(attributes={"color": "red", "font-size": "16px"}, content="Hello")
    assert txt.content == "Hello"
    assert txt.attrs["color"] == "red"
    assert txt.attrs["font-size"] == "16px"
    
    mjml_content = txt.render_mjml()
    assert 'color="red"' in mjml_content
    assert 'font-size="16px"' in mjml_content
    assert "Hello" in mjml_content


def test_leaf_tag_no_positional_children():
    # Leaf tags only have attributes and content parameters
    # Passing a positional arg should fail
    with pytest.raises(TypeError):
        text(section(content="child_not_allowed"))


def test_button_is_leaf_tag():
    btn = button(attributes={"href": "https://example.com"}, content="Click Me")
    assert btn.tagName == "mj-button"
    assert btn.content == "Click Me"
    assert btn.attrs["href"] == "https://example.com"
    
    mjml_content = btn.render_mjml()
    assert 'href="https://example.com"' in mjml_content
    assert "Click Me" in mjml_content
    assert "<mj-button" in mjml_content


def test_accordion_structure():
    acc = accordion(
        accordion_element(
            accordion_title(content="Title 1"),
            accordion_text(content="Text 1")
        )
    )
    assert acc.tagName == "mj-accordion"
    assert len(acc.children) == 1
    assert acc.children[0].tagName == "mj-accordion-element"


def test_navbar_structure():
    nav = navbar(
        navbar_link(attributes={"href": "/"}, content="Home"),
        navbar_link(attributes={"href": "/about"}, content="About")
    )
    assert nav.tagName == "mj-navbar"
    assert len(nav.children) == 2


def test_social_structure():
    soc = social(
        social_element(attributes={"href": "https://facebook.com"}, content="Facebook"),
        social_element(attributes={"href": "https://twitter.com"}, content="Twitter")
    )
    assert soc.tagName == "mj-social"
    assert len(soc.children) == 2


def test_carousel_structure():
    car = carousel(
        carousel_image(attributes={"src": "image1.jpg"}),
        carousel_image(attributes={"src": "image2.jpg"})
    )
    assert car.tagName == "mj-carousel"
    assert len(car.children) == 2


def test_raw_tag():
    r = raw(content="<div>Custom HTML</div>")
    assert r.tagName == "mj-raw"
    assert r.content == "<div>Custom HTML</div>"
    
    mjml_content = r.render_mjml()
    assert mjml_content == "<mj-raw>\n<div>Custom HTML</div>\n</mj-raw>"


def test_table_tag():
    tbl = table(content="<table><tr><td>Cell</td></tr></table>")
    assert tbl.tagName == "mj-table"
    assert "<table>" in tbl.content
    
    mjml_content = tbl.render_mjml()
    assert "<mj-table>" in mjml_content
    assert "<table><tr><td>Cell</td></tr></table>" in mjml_content


def test_mjml_full_document():
    doc = mjml(
        head(),
        body(
            section(
                column(
                    text(content="Hello World")
                )
            )
        )
    )
    assert doc.tagName == "mjml"
    assert len(doc.children) == 2
    assert doc.children[0].tagName == "mj-head"
    assert doc.children[1].tagName == "mj-body"


def test_image_tag():
    img = image(attributes={"src": "https://example.com/image.jpg", "alt": "Test Image"})
    assert img.tagName == "mj-image"
    assert img.attrs["src"] == "https://example.com/image.jpg"
    assert img.attrs["alt"] == "Test Image"
    
    mjml_content = img.render_mjml()
    assert 'src="https://example.com/image.jpg"' in mjml_content
    assert 'alt="Test Image"' in mjml_content
    assert "<mj-image" in mjml_content


def test_attributes_container_with_mj_all_and_classes():
    attrs = mj_attributes(
        mj_all(attributes={"font-family": "Arial"}),
        mj_class(attributes={"name": "blue", "color": "blue"}),
        mj_class(attributes={"name": "big", "font-size": "20px"})
    )
    
    assert attrs.tagName == "mj-attributes"
    assert len(attrs.children) == 3
    assert attrs.children[0].tagName == "mj-all"
    assert attrs.children[1].tagName == "mj-class"
    assert attrs.children[2].tagName == "mj-class"
    
    mjml_content = attrs.render_mjml()
    assert "<mj-attributes>" in mjml_content
    assert "<mj-all" in mjml_content
    assert 'font-family="Arial"' in mjml_content
    assert 'name="blue"' in mjml_content
    assert 'name="big"' in mjml_content


def test_component_with_mj_class_attribute():
    txt = text(attributes={"mj-class": "blue big"}, content="Hello World!")
    assert txt.attrs["mj-class"] == "blue big"
    
    mjml_content = txt.render_mjml()
    assert 'mj-class="blue big"' in mjml_content
    assert "Hello World!" in mjml_content


def test_full_document_with_attributes():
    doc = mjml(
        head(
            mj_attributes(
                text(attributes={"padding": "0"}),
                mj_class(attributes={"name": "blue", "color": "blue"}),
                mj_class(attributes={"name": "big", "font-size": "20px"}),
                mj_all(attributes={"font-family": "Arial"})
            )
        ),
        body(
            section(
                column(
                    text(attributes={"mj-class": "blue big"}, content="Hello World!")
                )
            )
        )
    )
    
    assert doc.tagName == "mjml"
    head_tag = doc.children[0]
    assert head_tag.tagName == "mj-head"
    
    attrs_tag = head_tag.children[0]
    assert attrs_tag.tagName == "mj-attributes"
    assert len(attrs_tag.children) == 4
    
    mjml_content = doc.render_mjml()
    assert "<mj-attributes>" in mjml_content
    assert '<mj-text padding="0"' in mjml_content
    assert 'name="blue"' in mjml_content
    assert 'name="big"' in mjml_content
    assert 'font-family="Arial"' in mjml_content
    assert 'mj-class="blue big"' in mjml_content
