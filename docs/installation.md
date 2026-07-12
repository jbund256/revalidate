---
icon: lucide/package-open
---

# Installation

## From PyPI

Install with pip:

```shell
pip install revalidate
```

To confirm the installation succeeded, run:

```python
import revalidate
print(revalidate.__version__)
```

## From source

Clone the repository and install in editable mode:

```shell
git clone https://github.com/jbund256/revalidate.git
cd revalidate
pip install .
```

## For development

Clone the repository and install with development dependencies:

```shell
git clone https://github.com/jbund256/revalidate.git
cd revalidate
uv sync --extra dev
```

This installs the package along with dependencies for testing, linting, and documentation building.
