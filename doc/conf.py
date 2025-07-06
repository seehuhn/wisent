import sys, os, re

extensions = ['sphinx.ext.autodoc']
templates_path = []
source_suffix = {'.txt': 'restructuredtext'}
master_doc = 'index'

# General information about the project.
project = 'wisent'
copyright = '2012, Jochen Voss'
author = 'Jochen Voss'

# Import version from the package
sys.path.insert(0, os.path.abspath('../wisent_pkg'))
from version import VERSION
version = '.'.join(VERSION.split('.')[:2])  # Major.minor (e.g., "0.6")
release = VERSION  # Full version (e.g., "0.6.2")

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['html', 'web', 'latex', '_build']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for HTML output
# -----------------------

html_title = "Wisent Users' Manual"
html_theme = 'alabaster'
# html_use_modindex deprecated in Sphinx 1.0
html_use_index = True
html_copy_source = False

# Options for LaTeX output
# ------------------------

latex_elements = {
    'papersize': 'a4',
    'pointsize': '10pt',
    'fontpkg': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = [
  ('index', 'wisent.tex', "Wisent Users' Manual", 'Jochen Voss', 'howto'),
]

# If false, no module index is generated.
# latex_use_modindex deprecated in Sphinx 1.0
