# nbmail.compose

The `compose` module provides a high-level, Pythonic API for building HTML emails using simple building blocks. It's designed for data science workflows where you need to create professional-looking emails without writing raw HTML or MJML.

## Quick Start

```python
from nbmail.compose import compose_email, block_text, block_title, create_blocks

# Simple email
email = compose_email(
    body=block_text("Hello world!")
)

# Email with multiple blocks
email = compose_email(
    title="Weekly Report",
    body=create_blocks(
        block_text("Welcome to this week's update!"),
        block_text("Here's what's new...")
    )
)
```

## Architecture

The compose module is built on three main concepts:

1. **Blocks** - Individual content units (text, images, plots, spacers, markdown)
2. **BlockList** - Collections of blocks that can be rendered together
3. **compose_email()** - The main entry point that converts blocks to MJML and then to Email objects

### Why Blocks?

Blocks provide a simple, composable abstraction over MJML's more complex tag structure. They encapsulate common email patterns (text sections, images, spacers) in an easy-to-use API.

### MJML Under the Hood

Blocks compile to MJML tags internally. MJML provides:
- Responsive design by default
- Cross-client compatibility
- Semantic structure (sections, columns, etc.)

### Inline Attachments

Local images are read as bytes and stored in `Email.inline_attachments` as base64 strings. During sending, these are converted to CID references in the MIME structure.

### Jupyter Display Support

Blocks and BlockLists implement `_repr_html_()` for rich display in notebooks:

```python
# In a Jupyter notebook:
block = block_text("Preview me!")
block  # Automatically renders as HTML
```

## Dependencies

**Required:**
- `markdown` - For Markdown processing in text blocks

**Optional:**
- `plotnine` - For `block_plot()` functionality



## API Reference

Complete API documentation is available in the [nbmail reference docs](https://posit-dev.github.io/nbmail/reference/).
