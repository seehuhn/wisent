import sys, os, re

extensions = [ ]
templates_path = [ 'templates' ]
source_suffix = '.txt'
master_doc = 'index'

# General information about the project.
project = 'wisent'
copyright = '2012, Jochen Voss'

m = re.search(r'AC_INIT\(wisent, *(([0-9]+\.[0-9]+)[^, ]*),',
              open("../../configure.ac", encoding="utf-8").read(),
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

html_theme = 'default'
html_theme_options = {
    "rightsidebar": "true",
    "footerbgcolor": "#B4C981",  # Background color for the footer line.
    "footertextcolor": "black",   # Text color for the footer line.
    "sidebarbgcolor": "#D4D991",  # Background color for the sidebar.
    "sidebartextcolor": "black",  # Text color for the sidebar.
    "sidebarlinkcolor": "#C00000", # Link color for the sidebar.
    "relbarbgcolor": "#B4C981", # Background color for the relation bar.
    "relbartextcolor": "black",   # Text color for the relation bar.
    "relbarlinkcolor": "#C00000", # Link color for the relation bar.
    "bgcolor": "#DBDEB7",         # Body background color.
    "textcolor": "black",         # Body text color.
    "linkcolor": "#C00000",       # Body link color.
    "headbgcolor": "#DBDEB7",     # Background color for headings.
    "headtextcolor": "black",     # Text color for headings.
    "headlinkcolor": "black",     # Link color for headings.
    "codebgcolor": "white",       # Background color for code blocks.
    "codetextcolor": "black",     # Default text color for code blocks
    # "bodyfont": "", # (CSS font-family): Font for normal text.
    # "headfont": "", # (CSS font-family): Font for headings.
}
