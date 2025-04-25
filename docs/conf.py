# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from importlib.metadata import version as get_version

project = "kensho-kfinance"
copyright = "2025, Kensho Technologies"
author = "Kensho Technologies"


# borrowed from here:
# https://setuptools-scm.readthedocs.io/en/latest/usage/#usage-from-sphinx
release: str = get_version(project)
# for example take major/minor
version: str = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# borrowed from internal Kensho Sphinx configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.githubpages",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    # 3rd party extensions
    # m2r2 is to add support to .md files specifically to include README.md files.
    # See this discussion: https://github.com/sphinx-doc/sphinx/issues/7000
    "m2r2",
    # A ReadTheDocs theme for Sphinx
    "sphinx_rtd_theme",
]

napoleon_google_docstring = True
napoleon_use_ivar = True

autosummary_generate = True

# Don't prepend module path prefixes to function definitions. Makes automodule docs less cluttered
add_module_names = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["templates"]

# The suffix of source filenames.
source_suffix = [".rst", ".md"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"

# https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html
html_theme_options = {"body_min_width": 0, "body_max_width": "none"}

# https://www.sphinx-doc.org/en/1.4.9/config.html#confval-html_sidebars
html_sidebars = {"**": ["globaltoc.html", "relations.html", "searchbox.html"]}
