# Wisent Python 3 Migration Plan

## Executive Summary

This document outlines the migration of Wisent (LR(1) parser generator) from Python 2 to Python 3. The migration is split into **two focused projects** to minimize risk and ensure thorough execution.

**Current State:** Wisent 0.6.2 is completely incompatible with Python 3 (syntax errors prevent import)  
**Migration Strategy:** Two-phase approach prioritizing core functionality first, then infrastructure improvements  
**Risk Level:** High (due to code generation complexity)

## Migration Strategy: Two-Project Approach

### **Project Alpha: Core Python 3 Migration**
**Goal:** Make Wisent fully functional on Python 3  
**Scope:** Core parser generation functionality only  
**Success Criteria:** Generated parsers work identically to Python 2 version  

### **Project Beta: Infrastructure Modernization** 
**Goal:** Modern tooling, security fixes, and distribution  
**Scope:** Security vulnerabilities, PyPI packaging, documentation updates  
**Success Criteria:** Professional Python 3 release with modern infrastructure  

## Critical Architecture Considerations

### Code Generation System
Wisent uses `inspect.getsource()` to extract Python source code from `template.py` and inject it into generated parsers. This means:
- **`template.py` is the most critical file** - any bugs affect ALL generated parsers
- **Generated parsers are standalone** - they contain extracted template code
- **Examples cannot be manually edited** - must be regenerated from .wi grammar files

### Dual Nature of template.py
The `template.py` file serves two purposes:
1. **Python module** imported by the generator (`import template`)
2. **Source code template** extracted via `inspect.getsource(template.Parser.method)`

Both aspects must work perfectly on Python 3.

---

# Project Alpha: Core Python 3 Migration

## Phase 1: Basic Syntax Compatibility

**Goal:** Fix syntax errors that prevent Python 3 import  
**Risk:** Medium - Tool becomes minimally functional  
**Success Criteria:** All core modules import successfully on Python 3

### 1.1 Exception Handling Syntax

**Files to modify:**
- `wisent.py` (3 instances)
- `check1.py` (1 instance)
- `grammar.py` (1 instance)
- `template.py` (affects all generated parsers)

**Changes:**
```python
# Before (Python 2)
except IOError, e:
except p.ParseErrors, e:

# After (Python 3)
except IOError as e:
except p.ParseErrors as e:
```

### 1.2 Print Statement Conversion

**Files to modify:**
- `wisent.py` (6 instances: 3 print + 3 print >>sys.stderr)
- `check1.py` (8+ print statements)
- `check2.py` (2 print statements)
- `grammar.py` (1 print >>sys.stderr)
- `template.py` (CRITICAL - affects all generated parsers)

**Changes:**
```python
# Before (Python 2)
print "message"
print >>sys.stderr, "error"

# After (Python 3)
print("message")
print("error", file=sys.stderr)
```

### 1.3 Import sys for stderr

**Files to modify:**
- Ensure all files using `sys.stderr` have `import sys`

**Validation:**
```bash
python3 -c "import wisent, grammar, automaton, template, scanner, parser, helpers, text, version"
```

## Phase 2: Advanced Python 3 Compatibility

**Goal:** Address deeper Python 3 compatibility issues  
**Risk:** High - These changes affect core functionality  
**Success Criteria:** Core functionality works without syntax errors

### 2.1 String and Unicode Handling

**Critical Analysis Required:**
- Audit all `unicode()` function calls
- Review string vs bytes usage in grammar parsing
- Check file I/O operations for encoding issues

**Files to audit:**
- `wisent.py` - `unicode(text, "utf-8")` usage
- `template.py` - `unicode(tree[0])` usage  
- `grammar.py` - `unicode(msg)` usage
- All file operations throughout codebase

**Changes:**
```python
# Before (Python 2)
unicode(text, "utf-8")
unicode(tree[0])

# After (Python 3) - depends on context
text.decode("utf-8")  # if text is bytes
str(tree[0])          # if conversion needed
text                  # if already string
```

### 2.2 File I/O and Encoding

**Audit all file operations:**
- Check for missing encoding specifications
- Verify text vs binary mode usage
- Ensure consistent encoding handling

**Pattern to find:**
```python
# Before (Python 2)
fd = open(filename, "r")
fd = open(filename, "w")

# After (Python 3) - specify encoding
fd = open(filename, "r", encoding="utf-8")
fd = open(filename, "w", encoding="utf-8")
```

### 2.3 Iterator Protocol Updates

**Files to modify:**
- `template.py` (2 instances: `tokens.next()`)
- `parser.py` (2 instances: `tokens.next()`)
- Generated parsers inherit from template.py

**Changes:**
```python
# Before (Python 2)
lookahead = tokens.next()

# After (Python 3)
lookahead = next(tokens)
```

### 2.4 Dictionary Iteration

**Files to modify:**
- `grammar.py` (1 instance: `self.list.iteritems()`)
- `automaton.py` (multiple instances: `dict.iteritems()`)

**Changes:**
```python
# Before (Python 2)
for key, value in dict.iteritems():
    pass

# After (Python 3)
for key, value in dict.items():
    pass
```

### 2.5 Integer Division Review

**Comprehensive audit needed:**
- Search for `/` operator usage
- Verify intended behavior (true division vs floor division)
- Ensure no breaking changes in grammar parsing logic

## Phase 3: Template System Migration

**Goal:** Make template.py fully Python 3 compatible  
**Risk:** HIGHEST - affects all generated parsers  
**Success Criteria:** Generated parsers work correctly on Python 3

### 3.1 Template Code Extraction Verification

**Critical Testing:**
- Verify `inspect.getsource()` works identically in Python 3
- Test extracted code is syntactically valid Python 3
- Ensure no Python 2 artifacts remain in extracted code

### 3.2 Generated Parser Testing

**Comprehensive validation:**
- Generate parsers from all example grammars
- Test generated parsers import and run correctly
- Compare output with Python 2 version (if available)

**Test procedure:**
```bash
# Generate test parser
python3 wisent.py examples/calculator/calculator.wi -o test_parser.py

# Test parser functionality
python3 -c "import test_parser; print('Parser import successful')"

# Test actual parsing
python3 examples/calculator/calc.py
```

## Phase 4: Input Function Migration

**Goal:** Update examples that use raw_input()  
**Risk:** Low - affects examples only  
**Success Criteria:** All examples work on Python 3

**Files to modify:**
- `examples/calculator/calc.py`
- Any other examples using `raw_input()`

**Changes:**
```python
# Before (Python 2)
s = raw_input("calc: ")

# After (Python 3)
s = input("calc: ")
```

## Phase 5: Core Testing and Validation

**Goal:** Comprehensive testing of migrated functionality  
**Risk:** Medium - validation phase  
**Success Criteria:** All core functionality verified working

### 5.1 Test Suite Migration

**Files to update:**
- `check1.py` - parser generation tests
- `check2.py` - scanner tests

**Testing procedure:**
```bash
# Run test suite
python3 check1.py
python3 check2.py

# Verify no errors
echo $?  # Should be 0
```

### 5.2 Example Regeneration and Testing

**CRITICAL:** Examples cannot be manually edited - must be regenerated

**Procedure:**
```bash
# Regenerate all examples
cd examples/calculator
python3 ../../wisent.py calculator.wi -o parser.py
python3 ../../wisent.py calculator.wi -e calc.py

cd ../css
python3 ../../wisent.py css.wi -o parser.py

cd ../email  
python3 ../../wisent.py parser.wi -o parser.py

# Test each example
cd calculator
python3 calc.py
# Interactive test: enter "2 + 3 * 4", expect "14"
```

### 5.3 Comprehensive Testing Matrix

**Test each combination:**
- Grammar parsing (all .wi files)
- Parser generation (all examples)
- Generated parser execution
- Error handling and recovery
- Debug output (-d flag)
- Complex grammars (JavaScript, CSS examples)

## Phase 6: Build System Updates

**Goal:** Update build system for Python 3  
**Risk:** Low - infrastructure changes  
**Success Criteria:** Installation and build work on Python 3

### 6.1 GNU Autotools Updates

**Files to modify:**
- `configure.ac` - Python version requirements
- `Makefile.am` - Python 3 module paths

**Changes in configure.ac:**
```bash
# Update Python version requirement
AM_PATH_PYTHON([3.6])  # Require Python 3.6+
```

### 6.2 Shebang Updates

**Files to modify:**
- `wisent.py` (generated version)
- `check1.py`
- `check2.py`
- All example scripts

**Changes:**
```python
# Before
#!/usr/bin/env python

# After  
#!/usr/bin/env python3
```

### 6.3 Installation Testing

**Validation:**
```bash
# Clean build test
make clean
./configure
make
make check
make install

# Verify installation
wisent --version
```

## Project Alpha Success Criteria

- [ ] All core modules import on Python 3
- [ ] Test suite passes completely
- [ ] All examples regenerate without errors
- [ ] Generated parsers handle complex grammars correctly
- [ ] Build system installs properly
- [ ] No Python 2 dependencies remain

---

# Project Beta: Infrastructure Modernization

*To be executed after Project Alpha is complete and stable*

## Phase 7: Security Vulnerability Resolution

**Goal:** Fix jQuery security vulnerabilities through Sphinx modernization  
**Risk:** Low - documentation only  
**Success Criteria:** All security alerts resolved

### 7.1 Sphinx Environment Update

**Current State:**
- Documentation uses Sphinx with jQuery 1.12.4
- Security vulnerabilities in generated documentation files

**Action Plan:**
```bash
# Check current Sphinx version
sphinx-build --version

# Update Sphinx to latest version
pip3 install --upgrade sphinx

# Verify updated version
sphinx-build --version
```

### 7.2 Documentation Regeneration

```bash
# Clean old generated files
cd doc/
rm -rf html/ web/html/ web/cache/

# Regenerate main documentation
sphinx-build -b html -d web/cache -c . . html/

# Regenerate web documentation
sphinx-build -b html -d web/cache -c web . web/html/

# Verify jQuery is updated to secure version
head -5 html/_static/jquery.js
```

### 7.3 Security Verification

```bash
# Verify jQuery version is now secure (3.x+)
grep -i "jquery.*v[0-9]" doc/html/_static/jquery.js

# Verify security alerts are resolved
gh api repos/seehuhn/wisent/dependabot/alerts --jq 'length'
# Should return 0 after GitHub rescans
```

## Phase 8: GitHub Issue Resolution

### 8.1 Issue #1: Installation Documentation

**Goal:** Complete installation documentation with autogen.sh step

**Files to create/modify:**
- `README` - Add Python 3 requirements
- `INSTALL` - Complete installation guide  
- `INSTALLATION.md` - Comprehensive guide

**Example content:**
```markdown
# Installation Instructions

## Prerequisites
- Python 3.6 or later
- GNU Autotools (autoconf, automake, libtool)

## Installation from Source
```bash
./autogen.sh    # Generate configure script
./configure
make
make check      # Run tests
make install
```

## Development Installation
```bash
./autogen.sh
./configure --prefix=/usr/local
make
# Test before installing
./wisent --version
make install
```
```

### 8.2 Issue #2: PyPI Release Preparation

**Goal:** Prepare package for PyPI distribution

**New files to create:**
- `setup.py` - Python packaging configuration
- `setup.cfg` - Package metadata
- `pyproject.toml` - Modern Python packaging
- `MANIFEST.in` - Include/exclude files for distribution
- `requirements-dev.txt` - Development dependencies

**Development Dependencies:**
```txt
# requirements-dev.txt
sphinx>=5.0.0
twine>=4.0.0
build>=0.8.0
wheel>=0.37.0
```

**setup.py example:**
```python
#!/usr/bin/env python3

from setuptools import setup, find_packages
import re

# Read version from configure.ac
with open('configure.ac', 'r') as f:
    version_match = re.search(r'AC_INIT\(wisent, *([^,]*),', f.read())
    if version_match:
        version = version_match.group(1).strip()
    else:
        version = '1.0.0'

setup(
    name='wisent',
    version=version,
    description='LR(1) parser generator for Python',
    long_description=open('README').read(),
    long_description_content_type='text/plain',
    author='Jochen Voss',
    author_email='voss@seehuhn.de',
    url='https://github.com/seehuhn/wisent',
    packages=find_packages(),
    scripts=['wisent'],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
    ],
    keywords='parser generator LR LALR grammar compiler',
)
```

**PyPI Testing:**
```bash
# Test package build
python3 setup.py sdist bdist_wheel
python3 -m twine check dist/*

# Test installation
pip3 install dist/wisent-*.whl
wisent --version

# Upload to PyPI (when ready)
python3 -m twine upload dist/*
```

## Phase 9: Documentation Modernization

### 9.1 Sphinx Configuration Updates

**Files to modify:**
- `doc/conf.py`
- `doc/web/conf.py`

**Example updates:**
```python
# Modern Sphinx configuration
project = 'wisent'
copyright = '2024, Jochen Voss'
version = '1.0'
release = '1.0.0'

# Modern Sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

# Optional: Modern theme
html_theme = 'sphinx_rtd_theme'  # or keep 'default'
```

### 9.2 Documentation Content Updates

**Key updates:**
- Python 3.6+ requirement prominently displayed
- PyPI installation instructions: `pip install wisent`
- Complete installation guide including autogen.sh
- Migration notes for existing Python 2 users
- Comparison with other parser generators (PLY, etc.)

## Project Beta Success Criteria

- [ ] All 6 security alerts resolved (jQuery updated)
- [ ] GitHub Issue #1 resolved (installation docs complete)
- [ ] GitHub Issue #2 resolved (PyPI package ready)
- [ ] Documentation modernized and regenerated
- [ ] PyPI package builds and installs correctly
- [ ] Version tagged as 1.0.0 for Python 3 release

---

# Risk Mitigation and Quality Assurance

## Backup and Recovery Strategy

### Pre-Migration Backup
```bash
# Create complete backup before starting
git tag pre-python3-migration
git checkout -b python3-migration
```

### Incremental Checkpoints
```bash
# After each phase
git add .
git commit -m "Phase X completed: [description]"
git tag phase-X-complete
```

### Rollback Procedures
```bash
# Emergency rollback to pre-migration state
git checkout pre-python3-migration

# Rollback to specific phase
git checkout phase-X-complete

# Selective rollback of specific files
git checkout pre-python3-migration -- template.py
```

## Testing Strategy

### Automated Testing Framework
Create comprehensive test suite for migration validation:

1. **Parser Output Comparison Tool**
   - Generate parsers with both Python 2 and 3 versions
   - Compare AST output for identical inputs
   - Flag any differences for investigation

2. **Regression Testing Suite**
   - Test all example grammars automatically
   - Verify error handling behavior unchanged
   - Check performance hasn't degraded significantly

3. **Grammar Compatibility Matrix**
   - Test wide variety of grammar constructs
   - Include edge cases and unusual patterns
   - Verify all .wi files in examples/ directory

### Manual Testing Checklist

- [ ] All core modules import successfully
- [ ] wisent --version works
- [ ] wisent --help displays correctly
- [ ] Basic grammar parsing works
- [ ] Complex grammar parsing (JavaScript, CSS)
- [ ] Error messages are appropriate
- [ ] Debug output (-d flag) functions
- [ ] Generated parsers handle edge cases
- [ ] Examples run interactively
- [ ] Build system works (configure, make, install)

## Quality Gates

Each phase must pass these criteria before proceeding:

### Phase Completion Criteria
1. **All tests pass** - No regressions introduced
2. **Code review complete** - All changes reviewed for correctness
3. **Documentation updated** - Changes documented appropriately
4. **Backup created** - Recovery point established

### Final Migration Validation
```bash
# Comprehensive end-to-end test
./autogen.sh
./configure  
make clean
make
make check

# Test complex grammar generation
wisent examples/javascript/javascript.wi -o js_parser.py
python3 -c "import js_parser; print('JavaScript parser works')"

# Test documentation build
cd doc/
sphinx-build -b html -d web/cache -c . . html/

# Verify security status
gh api repos/seehuhn/wisent/dependabot/alerts --jq 'length'
```

## Migration Completion Criteria

The migration is **complete** when:

### Project Alpha (Core Migration)
- ✅ All Python 3 syntax compatibility issues resolved
- ✅ Template system generates working Python 3 parsers
- ✅ All examples regenerate and function correctly
- ✅ Test suite passes completely
- ✅ Build and installation system works

### Project Beta (Infrastructure)  
- ✅ All security alerts resolved
- ✅ Documentation modernized and regenerated
- ✅ PyPI package ready for distribution
- ✅ GitHub issues addressed
- ✅ Version 1.0.0 tagged and release-ready

This represents the **first Python 3 compatible release** of Wisent with modern infrastructure and resolved security issues.