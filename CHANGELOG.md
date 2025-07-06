# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - TBD

### Added
- Modern Python packaging with `setup.py` and `pyproject.toml`
- pip installation support (`pip install wisent`)
- Comprehensive test suite (`test_appel.py`)
- New JavaScript parser examples (ECMAScript and simplified JavaScript grammars)
- New example parsers with generated code
- Console script entry point for system-wide installation
- Improved documentation with markdown README

### Changed
- **BREAKING**: Restructured project into `wisent_pkg/` package for proper Python packaging
- **BREAKING**: Updated all imports to use package-relative imports
- **BREAKING**: Python 3.6+ now required (dropped Python 2 support)
- Moved all core modules into `wisent_pkg/` package
- Reorganized tests into standard `tests/` directory structure
- Updated shebang lines to use `python3` explicitly
- Improved build system integration with modern Python tooling

### Fixed
- Package structure for proper pip installation
- Import statements updated for package-relative imports
- Generated parser compatibility with Python 3
- Code cleanup to reduce pychecker warnings

### Removed
- Python 2 compatibility code
- Old build artifacts and temporary files
- GNU Autotools build system (configure.ac, Makefile.am, etc.)

## [0.6.2] - 2012-04-10

### Added
- Allow hyphens '-' in symbol names
- New email address parser example in examples directory

### Fixed
- Better error messages for symbols without finite expansion and some grammar errors
- Infinite loop detection in grammar rules
- Multiline strings and comments in grammar files

### Changed
- Renamed test file from `check.py` to `check1.py`
- Minor fixes and improvements

## [0.6.1] - 2010-09-16

### Added
- New scanner test suite (`check2.py`)

### Fixed
- Comments and multi-line strings in grammar files (broken in version 0.6)

## [0.6] - 2009-10-11

### Added
- UTF-8 encoded grammar file support
- New CSS parser example in examples/css/

### Fixed
- Minor bug fixes

## [0.5] - 2009-07-14

### Added
- User manual documentation
- Brackets "(" ... ")" for grouping in grammar files
- New "?" operator (zero or one copy of an expression) in grammar files
- Command line option `-o` to specify output file (instead of stdout)
- Optional example source code generation (command line option `-e`)

## [0.4] - 2008-03-21

### Added
- Conflict overrides functionality
- Command line option `-r` to replace nonterminal symbols with numbers in parser output

### Changed
- Efficiency improvements for both parser generator and generated parsers
- Removed manual parser type selection (command line option `-t`)
- Wisent now automatically generates efficient parsers for any LR(1) grammar
- Renamed `Parser.parse_tree` method to `Parser.parse`

## [0.3] - 2008-03-07

### Fixed
- Restored ability to exclude symbols from parse tree (accidentally lost feature)

## [0.2] - 2008-03-02

### Added
- LR(0) parser generation capability (using `-t` command line option)

### Fixed
- Bug fixes and improved error handling

## [0.1] - 2008-03-01

### Added
- Initial public release