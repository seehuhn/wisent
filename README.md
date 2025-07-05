# Wisent - LR(1) Parser Generator for Python

Wisent is an LR(1) parser generator for Python 3 that converts context-free grammars into Python code.

## Requirements

- Python 3.6 or later
- pip (Python package manager)

## Installation

### Method 1: Install via pip (Recommended)

The easiest way to install Wisent is using pip:

```bash
pip install wisent
```

Install for current user only:
```bash
pip install --user wisent
```

Upgrade to the latest version:
```bash
pip install --upgrade wisent
```

### Method 2: Install from Source

Install the latest development version from source:

```bash
git clone https://github.com/seehuhn/wisent.git
cd wisent
pip install .
```

For development installation (editable):
```bash
pip install -e .
```

### Method 3: Traditional Build System

For the traditional autotools build process:

```bash
./configure
make
make install
```

#### Build Dependencies

For building from source using autotools:
- autotools (autoconf, automake)
- Python 3.6+ development headers
- make

#### Detailed Build Steps

1. **Configure the build:**
   ```bash
   ./configure
   ```
   
   Specify installation prefix:
   ```bash
   ./configure --prefix=/usr/local
   ```

2. **Build the project:**
   ```bash
   make
   ```

3. **Run tests (optional):**
   ```bash
   make check
   ```

4. **Install:**
   ```bash
   make install
   ```

5. **Run without installing:**
   ```bash
   ./wisent --version
   ```

## Verification

After installation, verify that Wisent is working:

```bash
wisent --version
```

Expected output:
```
wisent 0.6.2
Copyright (C) 2008, 2009 Jochen Voss <voss@seehuhn.de>
...
```

## Usage

Generate a parser from a grammar file:
```bash
wisent grammar.wi
```

Get help:
```bash
wisent --help
```

## Examples

The installation includes several example grammars in the `examples/` directory:

- `examples/calculator/calculator.wi` - Simple calculator grammar
- `examples/css/css.wi` - CSS parser grammar  
- `examples/email/parser.wi` - Email address parser

Try the calculator example:
```bash
wisent examples/calculator/calculator.wi
```

## Troubleshooting

### Python Version Issues

Check your Python version:
```bash
python3 --version
```

Use python3 explicitly:
```bash
python3 -m pip install wisent
```

### Permission Issues

Install for current user only:
```bash
pip install --user wisent
```

Or use a virtual environment:
```bash
python3 -m venv wisent-env
source wisent-env/bin/activate  # On Windows: wisent-env\\Scripts\\activate
pip install wisent
```

### Build Issues

Install development tools:

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential python3-dev
```

**CentOS/RHEL:**
```bash
sudo yum install gcc python3-devel
```

**macOS:**
```bash
xcode-select --install
```

Regenerate build files:
```bash
./autogen.sh
./configure
make
```

## Development

### Setup

Clone and install in development mode:
```bash
git clone https://github.com/seehuhn/wisent.git
cd wisent
pip install -e .
```

### Testing

Run tests:
```bash
make check
```

### Documentation

Build documentation:
```bash
cd doc/
sphinx-build -b html . html/
```

## Uninstallation

Remove Wisent:
```bash
pip uninstall wisent
```

## Documentation

The complete Wisent manual can be found in the `doc/html/` subdirectory of the source archive or online at http://seehuhn.de/media/manuals/wisent/

## License

Wisent comes with NO WARRANTY, to the extent permitted by law. You may redistribute copies of Wisent under the terms of the GNU General Public License. For more information, see the COPYING file.

## Support

- **Bug reports:** Send to <voss@seehuhn.de> (include version from `wisent -V`)  
- **Homepage:** http://seehuhn.de/pages/wisent

---

Copyright (C) 2008, 2009 Jochen Voss <voss@seehuhn.de>