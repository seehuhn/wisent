# Wisent - LR(1) Parser Generator for Python

Wisent is an LR(1) parser generator for Python 3 that converts context-free grammars into Python code. It provides a simple way to build robust parsers for custom languages and data formats, making it ideal for compiler construction, configuration file parsing, and domain-specific language development.

## Installation

The easiest way to install Wisent is using pip, which will handle all dependencies automatically. For most users, a simple `pip install wisent-parser` is sufficient. If you need the latest development version or want to contribute to the project, you can install from source using git.

```bash
# Install from PyPI (recommended)
pip install wisent-parser

# Install from source for development
git clone https://github.com/seehuhn/wisent.git
cd wisent
pip install -e .
```

For users without administrator privileges, add the `--user` flag to install only for your account. Python 3.6 or later is required.

## Quick Start

After installation, you can immediately start generating parsers from grammar files. Wisent uses a simple grammar syntax with `.wi` file extensions. Here's how to get started:

```bash
# Check that Wisent is working
wisent --version

# Generate a parser from a grammar file
wisent your_grammar.wi -o parser.py

# Try the included calculator example
wisent examples/calculator/calculator.wi
```

The examples directory contains several ready-to-use grammars including a calculator, CSS parser, and email address parser that demonstrate different parsing techniques and language features.

## Testing Your Installation

To verify that everything is working correctly, run the included test suite. These tests validate both the parser generation process and the grammar tokenizer functionality:

```bash
python3 tests/test_parser_generation.py
python3 tests/test_scanner.py
```

Both tests should complete with success messages, indicating that your installation is ready for use.

## Grammar File Format

Wisent grammars use a straightforward syntax similar to BNF notation. Rules are defined with colons and alternatives separated by vertical bars. The grammar format supports modern features like UTF-8 encoding, hyphenated symbol names, grouping with parentheses, and optional expressions with the `?` operator.

```
rule_name: symbol1 symbol2 | alternative ;
optional_expr: required_part optional_part? ;
grouped: symbol1 ( group_a | group_b ) symbol2 ;
```

See the examples directory and online documentation for complete grammar examples and advanced features.

## Documentation and Support

Complete documentation including a tutorial and reference manual is available online at http://seehuhn.de/media/manuals/wisent/. For bug reports or questions, contact <voss@seehuhn.de> and include the output of `wisent --version`.

## License

Wisent is free software distributed under the GNU General Public License. It comes with absolutely no warranty to the extent permitted by law. See the COPYING file for complete license terms.

---
Copyright (C) 2008, 2009 Jochen Voss