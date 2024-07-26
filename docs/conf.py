#!/usr/bin/env python
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

import configparser_override

# Execute as file cwd
sys.path.insert(0, os.path.abspath(".."))

project = "configparser_override"
copyright = "2024, Richard Nordström"
author = "Richard Nordström"
release = configparser_override.__version__
version = configparser_override.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Pull in docstrings
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.coverage",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "myst_parser",  # Import markdown to rst
]

# If true display todos in docs
todo_include_todos = False

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
