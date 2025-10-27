# MJML core classes adapted from py-htmltools

## TODO: make sure Ending tags are rendered as needed
# https://documentation.mjml.io/#ending-tags 

from typing import Dict, Mapping, Optional, Sequence, Union
import warnings
from mjml import mjml2html


# Types for MJML
TagAttrValue = Union[str, float, bool, None]
TagAttrs = Union[Dict[str, TagAttrValue], "TagAttrDict"]
TagChild = Union["MJMLTag", str, float, None, Sequence["TagChild"]]


class TagAttrDict(Dict[str, str]):
    """
    MJML attribute dictionary. All values are stored as strings.
    """

    def __init__(
        self, *args: Mapping[str, TagAttrValue]
    ) -> None:
        super().__init__()
        for mapping in args:
            for k, v in mapping.items():
                if v is not None:
                    self[k] = str(v)

    def update(self, *args: Mapping[str, TagAttrValue]) -> None:
        for mapping in args:
            for k, v in mapping.items():
                if v is not None:
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
            if self.content is not None and not isinstance(self.content, (str, int, float)):
                raise TypeError(
                    f"<{tagName}> content must be a string, int, or float, "
                    f"got {type(self.content).__name__}"
                )
            
            # Validate attributes parameter type
            if attributes is not None and not isinstance(attributes, (dict, TagAttrDict)):
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
            if attributes is not None and not isinstance(attributes, (dict, TagAttrDict)):
                raise TypeError(
                    f"attributes must be a dict or TagAttrDict, got {type(attributes).__name__}. "
                    f"If you meant to pass children, use positional arguments for container tags."
                )
            
            # Collect children (for non-leaf tags only)
            for arg in args:
                if (
                    isinstance(arg, (str, float)) or arg is None or isinstance(arg, MJMLTag)
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

    def render_mjml(self, indent: int = 0, eol: str = "\n") -> str:
        """
        Render MJMLTag and its children to MJML markup.
        Ported from htmltools Tag rendering logic.
        """

        def _flatten(children):
            for c in children:
                if c is None:
                    continue
                elif isinstance(c, MJMLTag):
                    yield c
                elif isinstance(c, (str, float)):
                    yield c

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
                    child_strs.append(child.render_mjml(indent + 2, eol))
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
        return self.to_html()

    def __repr__(self) -> str:
        return self.render_mjml()

    def to_html(self, **mjml2html_kwargs):
        """
        Render MJMLTag to HTML using mjml2html.
        
        If this is not a top-level <mjml> tag, it will be automatically wrapped
        in <mjml><mj-body>...</mj-body></mjml> with a warning.
        
        Parameters
        ----------
        **mjml2html_kwargs
            Additional keyword arguments to pass to mjml2html
            
        Returns
        -------
        str
            Result from mjml2html containing html content
        """
        if self.tagName == "mjml":
            # Already a complete MJML document
            mjml_markup = self.render_mjml()
        elif self.tagName == "mj-body":
            # Wrap only in mjml tag
            warnings.warn(
                "to_html() called on <mj-body> tag. "
                "Automatically wrapping in <mjml>...</mjml>. "
                "For full control, create a complete MJML document with the mjml() tag.",
                UserWarning,
                stacklevel=2
            )
            wrapped = MJMLTag("mjml", self)
            mjml_markup = wrapped.render_mjml()
        else:
            # Warn and wrap in mjml/mj-body
            warnings.warn(
                f"to_html() called on <{self.tagName}> tag. "
                "Automatically wrapping in <mjml><mj-body>...</mj-body></mjml>. "
                "For full control, create a complete MJML document with the mjml() tag.",
                UserWarning,
                stacklevel=2
            )
            # Wrap in mjml and mj-body
            wrapped = MJMLTag("mjml", MJMLTag("mj-body", self))
            mjml_markup = wrapped.render_mjml()
        
        return mjml2html(mjml_markup, **mjml2html_kwargs)
