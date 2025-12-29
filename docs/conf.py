"""Sphinx configuration."""

project = "HERA CLI Utils"
author = "Steven Murray"
copyright = "2023, Steven Murray"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
