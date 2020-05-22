# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Imports and Path setup ---------------------------------------------------

import sys, os, re
import datetime

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# Root of the package
sys.path.insert(1, os.path.abspath("{}".format(os.getenv("PYTHONSOURCE"))))
# Scripts directory
sys.path.insert(
    1, os.path.abspath("{}/gempython/scripts".format(os.getenv("PYTHONSOURCE")))
)

import sphinx_rtd_theme


# -- Project information -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# General information about the project.

# List all authors here
authorlist = [
    "Cameron Bravo",
    "Mykhailo Dalchenko",
    "Brian Dorney",
    "Andrew Michael Levin",
    "Louis Moureaux",
    "Jared Sturdy",
]

project = u"gempython.vfatqc"
authors = ", ".join(authorlist)
copyright = u"2016—{:d} {:s}".format(datetime.date.today().year, authors)

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The full version, including alpha/beta/rc tags.
release = os.popen("git describe --abbrev=6 --dirty --always --tags").read().strip()
try:
    release = re.sub("^v", "", release,)  #'1.0.0'
    # The short X.Y version.
    version = "{0}.{1}".format(*release.split("."))  #'1.0'
except Exception as e:
    print(e)
    version = "untagged-{0}".format(release)
    pass  # release = "0.0.0"

print("Version {}".format(version))
print("Release {}".format(release))


# -- General configuration ----------------------------------------------------

# # Tell sphinx what the primary language being documented is.
# primary_domain = "cpp"

# # Tell sphinx what the pygments highlight language should be.
# highlight_language = "cpp"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = "index"

# The reST default role (used for this markup: `text`) to use for all documents.
# default_role = None

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Extension configuration --------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    ## sphinx extensions
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.imgmath",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    ## sphinxcontrib
    "sphinxcontrib.napoleon",
    "sphinxcontrib.srclinks",
    ## sphinx external
    "sphinx_copybutton",
    "sphinx_rtd_theme",
    "sphinx_tabs.tabs",
    "m2r",
]

extensions += ["autoapi.extension"]

## -- autoapi python configuration --------------------------------------------

autoapi_type = "python"
autoapi_python_use_implicit_namespaces = True
autoapi_dirs = [
    "{}/gempython".format(os.getenv("PYTHONSOURCE"))
]
autoapi_add_toctree_entry = False
autoapi_keep_files = True
autoapi_options = [
    "members",
    "undoc-members",
    "private-members",
    "show-inheritance",
    "special-members",
    "show-inheritance-diagram",
    "show-module-summary",
]
autoapi_ignore = ["*migrations*", "*conf.py", "*setup.py"]
autoapi_template_dir = "_templates/autoapi"


## -- other extension configuration -------------------------------------------

# Disable numpy docstrings for Napoleon, because they eat headers such as
# "Examples"
napoleon_numpy_docstring = False

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


# -- Options for HTML output --------------------------------------------------

html_context = {
    "display_github": True,
    "github_host": "github.com",
    "github_user": "cms-gem-daq-project",
    "github_repo": "vfatqc-python-scripts",
    "github_version": "release/legacy-2.7",
    "conf_py_path": "/doc/source/",
    "last_updated": "{}".format(os.popen("date -u +'%a %b %d %Y %T %Z'").read().strip()),
    "commit": "{}".format(os.popen("git describe --abbrev=8 --dirty --always").read().strip()),
}

html_show_sourcelink = True

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = "vfatqc: Python Tools for Interacting with GEM Electronics"

# A shorter title for the navigation bar.  Default is the same as html_title.
html_short_title = "vfatqc"

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
# html_logo = None

## Show only the logo at the top of the sidebar
# logo_only

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = None

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    "navigation_depth": 50,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
# html_extra_path = ["../build/html"]

# Custom CSS
# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "{}/css/rtd-custom.css".format(os.getenv("GEM_DOCS_URL")),
]

# Custom JavaScript
# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_js_files = [
    # # enable for arrow key navigation
    # "{}/scripts/js/guides-navigation.js".format(os.getenv("GEM_DOCS_URL")),
]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = '%b %d, %Y'

# If true, the index is split into individual pages for each letter.
# html_split_index = False


# -- Options for HTMLHelp output ----------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "vfatqc-doc"


# -- Options for LaTeX output -------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    ("index", "vfatqc.tex", u"VFATQC Documentation", authors, "manual",),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# If true, show page references after internal links.
# latex_show_pagerefs = False

# If true, show URL addresses after external links.
# latex_show_urls = False

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_domain_indices = True


# -- Options for manual page output -------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ("index", "vfatqc", u"VFATQC Documentation", authors, 1),
    (
        "autoapi/dacScanV3/index",
        "dacScanV3.py",
        u"Perform a VFAT3 DAC scan on all unmasked optohybrids",
        authors,
        1,
    ),
    (
        "autoapi/ultrLatency/index",
        "ultraLatency.py",
        u"Perform a Latency Scan",
        authors,
        1,
    ),
    (
        "autoapi/monitorTemperatures/index",
        "monitorTemperatures.py",
        u"Record Temperature Data",
        authors,
        1,
    ),
    (
        "autoapi/checkSbitMappingAndRate/index",
        "checkSbitMappingAndRate.py",
        u"Investigate sbit Mapping and Rate Measurement",
        authors,
        1,
    ),
    ("autoapi/sbitReadOut/index", "sbitReadOut.py", u"Readout sbits", authors, 1),
    (
        "autoapi/sbitThreshScan/index",
        "sbitThreshScan.py",
        u"Launch an Sbit Rate vs. `CFG_THR_ARM_DAC` Scan",
        authors,
        1,
    ),
    (
        "autoapi/ultraScurve/index",
        "ultraScurve.py",
        u"Launch an Scurve Scan",
        authors,
        1,
    ),
    (
        "autoapi/ultraThreshold/index",
        "ultraThreshold.py",
        u"Launch a Threshold DAC Scan",
        authors,
        1,
    ),
    ("autoapi/trimChamber/index", "trimChamber.py", u"Launch a Trim Run", authors, 1),
    (
        "autoapi/iterativeTrim/index",
        "iterativeTrim.py",
        u"Launch an Iterative Trim Run",
        authors,
        1,
    ),
]

# If true, show URL addresses after external links.
# man_show_urls = False


# -- Options for Texinfo output -----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "vfatqc",
        u"VFATQC Documentation",
        authors,
        "vfatqc",
        "VFATQC Scanning tools.",
        "Miscellaneous",
    ),
]

# Documents to append as an appendix to all manuals.
# texinfo_appendices = []

# If false, no module index is generated.
# texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'


# This config value contains the locations and names of other projects that
# should be linked to in this documentation.
intersphinx_mapping = {
    "cmsgemos": (os.getenv("EOS_SITE_URL") + "/docs/api/cmsgemos/latest", None,),
    "gemplotting": (os.getenv("EOS_SITE_URL") + "/docs/api/gemplotting/latest", None,),
    "ctp7_modules": (
        os.getenv("EOS_SITE_URL") + "/docs/api/ctp7_modules/latest",
        None,
    ),
    "reg_utils": (os.getenv("EOS_SITE_URL") + "/docs/api/reg_utils/latest", None,),
    "xhal": (os.getenv("EOS_SITE_URL") + "/docs/api/xhal/latest", None,),
}
