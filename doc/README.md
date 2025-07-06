# Wisent Documentation

This directory contains the Wisent users' manual.

## Overview

The manual is written using the [Sphinx documentation generator](https://www.sphinx-doc.org/). A pre-formatted version of the manual can be found in the `html/` sub-directory.

## Online Version

A copy of the manual can be found online at:
http://seehuhn.de/media/manuals/wisent/

## Building the Documentation

### Prerequisites

To rebuild the documentation, you will need:
- **Sphinx** version 0.6 or newer (though modern versions are recommended)
- **Python 3.6+** (required for Wisent)

Install Sphinx using:
```bash
pip install sphinx
```

### Build Commands

#### HTML Documentation

**Standard build:**
```bash
cd doc/
sphinx-build -b html -d web/cache -c . . html/
```

**Using the convenience script:**
```bash
cd doc/
./generate-web-doc
```

This script:
- Creates necessary directories (`web/html`, `web/cache`)
- Builds HTML documentation with proper permissions
- Uses the web configuration from `web/conf.py`

#### PDF Documentation

To generate a PDF version:
```bash
cd doc/
sphinx-build -b latex -d web/cache -c . . latex/
cd latex/
make
```

### Configuration

The documentation uses two configuration files:
- `conf.py` - Main configuration for standard HTML build
- `web/conf.py` - Configuration for web version (used by `generate-web-doc`)

### Output Directories

- `html/` - Standard HTML documentation
- `web/html/` - Web version HTML documentation (created by `generate-web-doc`)
- `web/cache/` - Sphinx cache directory
- `latex/` - LaTeX output (if generating PDF)
