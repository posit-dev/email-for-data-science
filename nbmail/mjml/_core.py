# MJML core classes adapted from py-htmltools

## TODO: make sure Ending tags are rendered as needed
# https://documentation.mjml.io/#ending-tags

from typing import Dict, Mapping, Optional, Sequence, Union
import warnings
from io import BytesIO
from mjml import mjml2html


# Types for MJML

TagAttrValue = Union[str, float, bool, None, bytes, BytesIO]
TagAttrs = Union[Dict[str, TagAttrValue], "TagAttrDict"]
TagChild = Union["MJMLTag", str, float, None, Sequence["TagChild"]]


class TagAttrDict(Dict[str, Union[str, bytes, BytesIO]]):
    """
    MJML attribute dictionary. Most values are stored as strings, but bytes/BytesIO are preserved.
    """

    def __init__(self, *args: Mapping[str, TagAttrValue]) -> None:
        super().__init__()
        for mapping in args:
            for k, v in mapping.items():
                if v is not None:
                    # Preserve bytes and BytesIO objects as-is for image processing
                    if isinstance(v, (bytes, BytesIO)):
                        self[k] = v
                    else:
                        self[k] = str(v)

    def update(self, *args: Mapping[str, TagAttrValue]) -> None:
        for mapping in args:
            for k, v in mapping.items():
                if v is not None:
                    # Preserve bytes and BytesIO objects as-is for image processing
                    if isinstance(v, (bytes, BytesIO)):
                        self[k] = v
                    else:
                        self[k] = str(v)


class MJMLTag:
    """
    MJML tag class.
    """

    def __init__(
        self,
        tagName: str,
        *args: TagChild,
        attributes: Optional[TagAttrs] = None,
        content: Optional[str] = None,
        _is_leaf: bool = False,
    ) -> None:
        self.tagName = tagName
        self.attrs = TagAttrDict()
        self.children = []
        self._is_leaf = _is_leaf

        # Runtime validation for leaf tags
        if self._is_leaf:
            # For leaf tags, treat the first positional argument as content if provided
            if args:
                if len(args) > 1:
                    raise TypeError(
                        f"<{tagName}> is a leaf tag and accepts only one positional argument for content."
                    )
                self.content = args[0]
            else:
                self.content = content

            # Validate content type
            if self.content is not None and not isinstance(
                self.content, (str, int, float)
            ):
                raise TypeError(
                    f"<{tagName}> content must be a string, int, or float, "
                    f"got {type(self.content).__name__}"
                )

            # Validate attributes parameter type
            if attributes is not None and not isinstance(
                attributes, (dict, TagAttrDict)
            ):
                raise TypeError(
                    f"attributes must be a dict or TagAttrDict, got {type(attributes).__name__}."
                )

            # Process attributes
            if attributes is not None:
                self.attrs.update(attributes)
        else:
            # For container tags
            self.content = content

            # Validate attributes parameter type
            if attributes is not None and not isinstance(
                attributes, (dict, TagAttrDict)
            ):
                raise TypeError(
                    f"attributes must be a dict or TagAttrDict, got {type(attributes).__name__}. "
                    f"If you meant to pass children, use positional arguments for container tags."
                )

            # Collect children (for non-leaf tags only)
            for arg in args:
                if (
                    isinstance(arg, (str, float))
                    or arg is None
                    or isinstance(arg, MJMLTag)
                ):
                    self.children.append(arg)
                elif isinstance(arg, Sequence) and not isinstance(arg, str):
                    self.children.extend(arg)

            # Process attributes
            if attributes is not None:
                self.attrs.update(attributes)

        # TODO: confirm if this is the case... I don't think it is
        # # If content is provided, children should be empty
        # if self.content is not None:
        #     self.children = []

    def _to_mjml(self, indent: int = 0, eol: str = "\n") -> str:
        """
        Render MJMLTag and its children to MJML markup.
        Ported from htmltools Tag rendering logic.
        
        Note: BytesIO/bytes in image src attributes are not supported by _to_mjml().
        Pass the MJMLTag directly to mjml_to_email() instead.
        """

        def _flatten(children):
            for c in children:
                if c is None:
                    continue
                elif isinstance(c, MJMLTag):
                    yield c
                elif isinstance(c, (str, float)):
                    yield c

        # Check for BytesIO/bytes in mj-image tags and raise clear error
        if self.tagName == "mj-image" and "src" in self.attrs:
            src_value = self.attrs["src"]
            if isinstance(src_value, (bytes, BytesIO)):
                raise ValueError(
                    "Cannot render MJML with BytesIO/bytes in image src attribute. "
                    "Pass the MJMLTag object directly to mjml_to_email() instead of calling _to_mjml() first. "
                    "Example: i_email = mjml_to_email(doc)"
                )

        # Build attribute string
        attr_str = ""
        if self.attrs:
            attr_str = " " + " ".join(f'{k}="{v}"' for k, v in self.attrs.items())

        # Render children/content
        inner = ""
        if self.content is not None:
            inner = str(self.content)
        else:
            child_strs = []
            for child in _flatten(self.children):
                if isinstance(child, MJMLTag):
                    child_strs.append(child._to_mjml(indent + 2, eol))
                else:
                    child_strs.append(str(child))
            if child_strs:
                inner = eol.join(child_strs)

        # Indentation
        pad = " " * indent
        if inner:
            return f"{pad}<{self.tagName}{attr_str}>{eol}{inner}{eol}{pad}</{self.tagName}>"
        else:
            return f"{pad}<{self.tagName}{attr_str}></{self.tagName}>"

    def _repr_html_(self):
        from ..ingress import mjml_to_email
        return mjml_to_email(self)._repr_html_()

    # TODO: make something deliberate
    def __repr__(self) -> str:
        warnings.warn(
            f"__repr__ not yet fully implemented for MJMLTag({self.tagName})",
            UserWarning,
            stacklevel=2,
        )
        return f"<MJMLTag({self.tagName})>"

    # warning explain that they are not to pass this to email
    def to_html(self, **mjml2html_kwargs) -> str:
        """
        Render MJMLTag to HTML using mjml2html.

        If this is not a top-level <mjml> tag, it will be automatically wrapped
        in <mjml><mj-body>...</mj-body></mjml> with a warning.

        Note: This method embeds all images as inline data URIs in the HTML.
        For email composition with inline attachments, use mjml_to_email() instead.

        Parameters
        ----------
        **mjml2html_kwargs
            Additional keyword arguments to pass to mjml2html

        Returns
        -------
        str
            Result from `mjml-python.mjml2html()` containing html content
        """
        if self.tagName == "mjml":
            # Already a complete MJML document
            mjml_markup = self._to_mjml()
        elif self.tagName == "mj-body":
            # Wrap only in mjml tag
            warnings.warn(
                "to_html() called on <mj-body> tag. "
                "Automatically wrapping in <mjml>...</mjml>. "
                "For full control, create a complete MJML document with the mjml() tag.",
                UserWarning,
                stacklevel=2,
            )
            wrapped = MJMLTag("mjml", self)
            mjml_markup = wrapped._to_mjml()
        else:
            # Warn and wrap in mjml/mj-body
            warnings.warn(
                f"to_html() called on <{self.tagName}> tag. "
                "Automatically wrapping in <mjml><mj-body>...</mj-body></mjml>. "
                "For full control, create a complete MJML document with the mjml() tag.",
                UserWarning,
                stacklevel=2,
            )
            # Wrap in mjml and mj-body
            wrapped = MJMLTag("mjml", MJMLTag("mj-body", self))
            mjml_markup = wrapped._to_mjml()

        return mjml2html(mjml_markup, **mjml2html_kwargs)
