#!/usr/bin/env python3
"""
Setup script for Wisent - LR(1) parser generator for Python
"""

import os
import re
from setuptools import setup, find_packages

# Read version from configure.ac
def get_version():
    with open("configure.ac", "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'AC_INIT\(wisent, *(([0-9]+\.[0-9]+)[^, ]*),', content, re.MULTILINE)
    if match:
        return match.group(1)
    return "0.6.2"

# Read README
def get_long_description():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

setup(
    name="wisent",
    version=get_version(),
    description="LR(1) parser generator for Python",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Jochen Voss",
    author_email="voss@seehuhn.de",
    url="http://seehuhn.de/pages/wisent",
    license="GPL-2.0-or-later",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "wisent=wisent_pkg.wisent:main",
        ],
    },
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
    ],
    keywords="parser generator lr1 lalr compiler",
    project_urls={
        "Bug Reports": "https://github.com/seehuhn/wisent/issues",
        "Source": "https://github.com/seehuhn/wisent",
    },
)