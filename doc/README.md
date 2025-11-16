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

```bash
cd doc/
sphinx-build -b html -c . . html/
```

#### PDF Documentation

To generate a PDF version:
```bash
cd doc/
sphinx-build -b latex -c . . latex/
cd latex/
make
```

### Configuration

The documentation uses `conf.py` for Sphinx configuration.

### Output Directories

- `html/` - HTML documentation
- `latex/` - LaTeX output (if generating PDF)
