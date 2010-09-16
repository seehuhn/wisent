import sys, os, re

extensions = []
templates_path = []
source_suffix = '.txt'
master_doc = 'index'

# General information about the project.
project = 'wisent'
copyright = '2010, Jochen Voss'

m = re.search(r'AC_INIT\(wisent, *(([0-9]+\.[0-9]+)[^, ]*),',
              open("../configure.ac").read(),
              re.MULTILINE)
version = m.group(2)
release = m.group(1)
del m

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = [ 'html', 'web', 'latex' ]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for HTML output
# -----------------------

html_title = "Wisent Users' Manual"
html_use_modindex = False
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
latex_use_modindex = False
