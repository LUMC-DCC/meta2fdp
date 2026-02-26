# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
from pathlib import Path
import tomllib

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
with open(pyproject_path, "rb") as f:
    pyproject_toml = tomllib.load(f)

# project metadata from pyproject.toml
project_metadata = pyproject_toml.get("project", {})

project = project_metadata.get("name", "meta2fdp")
author = ", ".join(
    [
        author["name"]
        for author in project_metadata.get(
            "authors", [{"name": "Karolis Cremers, Anna Niehues"}]
        )
    ]
)
copyright = "2026, Leiden University Medical Center (LUMC)"
release = project_metadata.get("version", "0.0.0")

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
