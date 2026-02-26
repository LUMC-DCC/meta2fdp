# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "meta2fdp"
copyright = "2026, Karolis Cremers, Anna Niehues"
author = "Karolis Cremers, Anna Niehues"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # for automatic documentation of Python modules
    "sphinx.ext.napoleon",  # for Google style docstrings
    "sphinx.ext.viewcode",  # for adding links to source code in the documentation
    "sphinx.ext.autosummary",  # for generating summary tables for modules, classes, and functions
    "sphinxcontrib.mermaid",  # for rendering Mermaid diagrams in the documentation
    "myst_parser",  # for parsing Markdown files
]
napoleon_google_docstring = True

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
