# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wisent is an LR(1) parser generator for Python that converts context-free grammars into Python code. It's a mature, stable project (version 0.6.2) built with GNU Autotools.

**Current State:**
- **Python 2 only** - Does not run on Python 3 (syntax errors prevent import)
- **Last major release:** April 10, 2012 (12+ years ago)
- **Development status:** Maintenance mode - minimal activity since 2012
- **Stability:** Very stable codebase with no recent breaking changes

## Critical Architecture Understanding

### Code Generation System (Most Important)
Wisent uses `inspect.getsource()` to extract Python source code from `template.py` and inject it into generated parsers:

- **`template.py` is the most critical file** - any bugs affect ALL generated parsers
- **Generated parsers are standalone** - they contain extracted template code
- **Examples cannot be manually edited** - must be regenerated from .wi grammar files

### Dual Nature of template.py
The `template.py` file serves two purposes:
1. **Python module** imported by the generator (`import template`)
2. **Source code template** extracted via `inspect.getsource(template.Parser.method)`

## Build System and Development Commands

**Prerequisites:**
- Python 2.7 (Python 3 not supported)
- GNU Autotools (autoconf, automake, libtool)

### Building the Project
```bash
./autogen.sh    # Generate configure script (often missing from docs)
./configure
make
make install
```

### Running Tests
```bash
make check
```
This runs the test suite consisting of:
- `check1.py` - Parser generation and parsing tests
- `check2.py` - Scanner/tokenizer tests

### Building Documentation
The project uses Sphinx for documentation generation:
- Documentation source in `doc/` 
- Built documentation in `doc/html/` and `doc/web/html/`
- Uses Sphinx with old jQuery 1.12.4 (security vulnerabilities)

```bash
cd doc/
sphinx-build -b html -d web/cache -c . . html/
./generate-web-doc  # Alternative build script
```

### Running Wisent
After building, the main executable is `wisent`:
```bash
./wisent [options] grammar_file
```

Key options:
- `-o FILE` - Output parser to FILE
- `-e FILE` - Generate example code to FILE
- `-d p` - Enable parser debugging
- `-r` - Replace nonterminals with numbers
- `-V` - Show version information

## Core Components

- **wisent.py** - Main entry point and command-line interface
- **grammar.py** - Grammar parsing and representation
- **automaton.py** - LR(1) automaton construction and parser generation
- **scanner.py** - Tokenizer for grammar files
- **parser.py** - Base parser classes and error handling
- **template.py** - **CRITICAL**: Code generation templates (affects all generated parsers)
- **helpers.py** - Utility functions
- **text.py** - Text processing utilities

## Grammar File Format

Grammar files use `.wi` extension with syntax like:
```
rule_name: symbol1 symbol2 | alternative ;
```

Features:
- UTF-8 encoding support (added in 0.6)
- Hyphens allowed in symbol names (added in 0.6.2)
- Brackets for grouping: `( expression )`
- Optional operator: `expression?`
- Comments and multi-line strings supported

## Code Generation Flow

1. Parse grammar file with `grammar.py`
2. Build LR(1) automaton with `automaton.py`
3. **Extract source code from `template.py`** using `inspect.getsource()`
4. **Inject template code into generated parser**
5. Optionally generate example usage code

## Examples Directory

The `examples/` directory contains various grammar examples:
- `calculator/` - Complete calculator with evaluator
- `css/` - CSS parser (added in 0.5)
- `email/` - Email address parser (added in 0.6.2)
- `javascript/` - JavaScript parser
- Various Appel textbook examples (appel3.*.wi)

**Important:** All `.py` files in examples are **generated** and should not be manually edited.

## Parser Error Handling

Generated parsers support sophisticated error recovery:
- `errcorr_pre` - Tokens to look ahead for error correction
- `errcorr_post` - Tokens to look behind for error correction
- Infinite loop detection in grammar rules (added in 0.6.1)
- Meaningful error messages with expected tokens

## Known Issues and Limitations

### Python 3 Incompatibility
- **Syntax errors** prevent import on Python 3
- **Print statements** instead of print() function
- **Exception handling** uses old `except Exception, e:` syntax
- **Iterator protocol** uses `iterator.next()` instead of `next(iterator)`
- **Dictionary iteration** uses `.iteritems()` instead of `.items()`
- **Unicode handling** uses `unicode()` function

### Security Vulnerabilities
- **6 open Dependabot alerts** for jQuery 1.12.4 in documentation
- All related to XSS vulnerabilities in generated Sphinx documentation
- Files affected: `doc/html/_static/jquery.js`, `doc/web/html/_static/jquery.js`

### GitHub Issues
- **Issue #1 (2014):** Installation documentation incomplete (missing autogen.sh step)
- **Issue #2 (2014):** Request for PyPI distribution

## Development History

- **2008-2012:** Active development period (87 commits)
- **2012:** Last major release (0.6.2) 
- **2012-2024:** Maintenance mode with minimal activity
- **2024:** Only 2 minor commits (jQuery update attempt, test driver change)

## Technical Debt

After 12+ years of minimal maintenance:
- No Python 3 compatibility
- Outdated dependencies (Sphinx, jQuery)
- Missing modern Python packaging (no setup.py, PyPI presence)
- Documentation gaps (installation process)
- Security vulnerabilities in documentation assets

## Working with This Codebase

### Before Making Changes
1. **Understand the template system** - changes to `template.py` affect all generated parsers
2. **Test with examples** - regenerate and test all parsers in `examples/`
3. **Python 2 required** - current code will not run on Python 3

### Testing Strategy
1. Run test suite: `python2 check1.py && python2 check2.py`
2. Test parser generation: `python2 wisent.py examples/calculator/calculator.wi -o test.py`
3. Test generated parser: `python2 -c "import test; print('OK')"`
4. Test examples: `cd examples/calculator && python2 calc.py`

### Code Generation Testing
Since generated parsers are the primary output:
1. Test all `.wi` files in examples directory
2. Verify generated parsers are syntactically valid
3. Compare parser behavior before/after changes
4. Test error handling and recovery mechanisms