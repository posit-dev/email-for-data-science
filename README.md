# nbmail

<!-- [![Python Versions](https://img.shields.io/pypi/pyversions/gt_extras.svg)](https://pypi.python.org/pypi/gt-extras) -->
<!-- [![PyPI](https://img.shields.io/pypi/v/gt-extras?logo=python&logoColor=white&color=orange)](https://pypi.org/project/gt-extras/) -->
<!-- [![PyPI Downloads](https://static.pepy.tech/badge/gt-extras)](https://pepy.tech/projects/gt-extras) -->
<!-- [![License](https://img.shields.io/github/license/posit-dev/email-for-data-science)](https://github.com/posit-dev/email-for-data-science/blob/main/LICENSE) -->

<!-- [![Tests](https://github.com/posit-dev/gt-extras/actions/workflows/ci_tests.yml/badge.svg)](https://github.com/posit-dev/gt-extras/actions/workflows/ci_tests.yml) -->
[![Documentation](https://img.shields.io/badge/docs-project_website-blue.svg)](https://posit-dev.github.io/email-for-data-science/reference/)
<!-- [![Repo Status](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip) -->
<!-- [![Contributors](https://img.shields.io/github/contributors/posit-dev/gt-extras)](https://github.com/posit-dev/gt-extras/graphs/contributors) -->
<!-- [![Codecov](https://codecov.io/gh/posit-dev/gt-extras/branch/main/graph/badge.svg)](https://codecov.io/gh/posit-dev/gt-extras) -->

> ⚠️ **nbmail is currently in development, expect breaking changes.**


### What is [nbmail](https://posit-dev.github.io/email-for-data-science/reference/)?

**nbmail** is a Python package for serializing, previewing, and sending email messages in a consistent, simple structure. It provides utilities to convert emails from different sources (Redmail, Yagmail, MJML, Quarto JSON) into a unified intermediate format, and send them via multiple backends (Gmail, SMTP, Mailgun, etc.).

The package is designed for data science workflows and Quarto projects, making it easy to generate, preview, and deliver rich email content programmatically.

<!-- ## Installation
Install the latest release from your local repo or PyPI:

```bash
pip install -e ./nbmail
```
-->

## Example Usage

```python
from nbmail import (
    quarto_json_to_email,
    Email,
    send_email_with_gmail,
)

# Read a Quarto email JSON file
email = quarto_json_to_email("email.json")

# Preview the email as HTML
email.write_preview_email("preview.html")

# Send the email via Gmail
send_email_with_gmail("your_email@gmail.com", "your_password", email)
```

## Features

- **Unified email structure** for serialization and conversion
- **Convert** emails from Redmail, Yagmail, MJML, and Quarto JSON
- **Send** emails via Gmail, SMTP, Mailgun, and more
- **Preview** emails as HTML files
- **Support for attachments** (inline and external)
- **Simple API** for integration in data science and reporting workflows

## Contributing
If you encounter a bug, have usage questions, or want to share ideas to make this package better, please feel free to file an [issue](https://github.com/posit-dev/email-for-data-science/issues).

<!-- 
## Code of Conduct
Please note that the **gt-extras** project is released with a [contributor code of conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).<br>By participating in this project you agree to abide by its terms. -->

<!-- ## 📄 License

**Great Tables** is licensed under the MIT license.

© Posit Software, PBC. -->

<!-- ## Citation
If you use **gt-extras** in your work, please cite the package:

```bibtex
@software{gt_extras,
authors = {Jules Walzer-Goldfeld, Michael Chow, and Rich Iannone},
license = {MIT},
title = {{gt-extras: Extra helpers for great-tables in Python.}},
url = {https://github.com/posit-dev/gt-extras}, version = {0.0.1}
}
``` -->

For more information, see the [docs](https://posit-dev.github.io/email-for-data-science/reference) or [open an issue](https://github.com/posit-dev/email-for-data-science/issues) with questions or suggestions!
