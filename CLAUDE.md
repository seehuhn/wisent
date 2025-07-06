# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wisent is an LR(1) parser generator for Python 3 that converts context-free grammars into Python code. It's a mature, stable project (version 0.6.2) with modern Python packaging.

**Current State:**
- **Python 3 compatible** - Fully migrated to Python 3.6+ with modern packaging
- **Last major release:** April 10, 2012 (12+ years ago)
- **Development status:** Recently migrated to Python 3 with active maintenance
- **Stability:** Very stable codebase with successful Python 3 migration
- **Current version:** 0.6.2 (verified in setup.py, pyproject.toml, and version files)

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
- Python 3.6+ (Python 2 no longer supported)
- pip (Python package manager)

### Building the Project

**Installation:**
```bash
pip install -e .    # Development install
# or
pip install .       # Regular install
```

**From PyPI (when available):**
```bash
pip install wisent
```

### Running Tests

```bash
python3 tests/test_parser_generation.py
python3 tests/test_scanner.py
```

This runs the test suite consisting of:
- `test_parser_generation.py` - Parser generation and parsing tests
- `test_scanner.py` - Scanner/tokenizer tests

### Building Documentation
The project uses Sphinx for documentation generation:
- Documentation source in `doc/`
- Built documentation in `doc/html/` and `doc/web/html/`

```bash
cd doc/
sphinx-build -b html -d web/cache -c . . html/
./generate-web-doc  # Alternative build script
```

### Running Wisent

**After pip install:**
```bash
wisent [options] grammar_file
# or
python3 -m wisent_pkg.wisent [options] grammar_file
```

Key options:
- `-o FILE` - Output parser to FILE
- `-e FILE` - Generate example code to FILE
- `-d p` - Enable parser debugging
- `-r` - Replace nonterminals with numbers
- `-V` - Show version information

## Core Components

**Package Structure:**
- **wisent_pkg/** - Main package directory containing all core modules
  - **wisent.py** - Main entry point and command-line interface
  - **grammar.py** - Grammar parsing and representation
  - **automaton.py** - LR(1) automaton construction and parser generation
  - **scanner.py** - Tokenizer for grammar files
  - **parser.py** - Base parser classes and error handling
  - **template.py** - **CRITICAL**: Code generation templates (affects all generated parsers)
  - **helpers.py** - Utility functions
  - **text.py** - Text processing utilities
  - **version.py** - Version information

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

## Working with This Codebase

### Before Making Changes
1. **Understand the template system** - changes to `wisent_pkg/template.py` affect all generated parsers
2. **Test with examples** - regenerate and test all parsers in `examples/`
3. **Python 3 required** - code now requires Python 3.6+
4. **Package imports** - use `from wisent_pkg.module import ...` for internal imports

### Testing Strategy
1. Run test suite: `python3 tests/test_parser_generation.py && python3 tests/test_scanner.py`
2. Test parser generation: `python3 -m wisent_pkg.wisent examples/calculator/calculator.wi -o test.py`
3. Test generated parser: `python3 -c "import test; print('OK')"`
4. Test examples: `cd examples/calculator && python3 calc.py`
5. Test console script: `wisent examples/calculator/calculator.wi -o test.py` (after pip install)

### Code Generation Testing
Since generated parsers are the primary output:
1. Test all `.wi` files in examples directory
2. Verify generated parsers are syntactically valid Python 3
3. Compare parser behavior before/after changes
4. Test error handling and recovery mechanisms
5. Verify all examples work with Python 3