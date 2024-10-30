# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from typing import Any

from sphinx.application import Sphinx
from sphinx.ext.autodoc import Options

project = "Ligare"
copyright = "2024, Aaron Holmes"
author = "Aaron Holmes"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

extensions = [
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": False,
    "special-members": "__init__",
}


def skip_member(
    app: Sphinx, what: str, name: str, obj: Any, skip: bool, options: Options
) -> bool:
    """
    Determines whether a member should be skipped during autodoc processing.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application instance.
    what : str
        The type of object being documented (e.g., 'class', 'method').
    name : str
        The name of the attribute or method.
    obj : Any
        The actual object representing the member.
    skip : bool
        Indicates if Sphinx would skip this member by default.
    options : Options
        The autodoc options for the current processing.

    Returns
    -------
    bool
        True to skip the member, False to include it in the documentation.
    """
    # prevent
    # WARNING: autodoc: failed to import attribute 'MiddlewareRequestDict.starlette.exception_handlers' from module 'Ligare.web.middleware.openapi';
    if name == "starlette.exception_handlers":
        return True
    return skip


def setup(app: Sphinx) -> None:
    """
    Connects the `skip_member` function to the `autodoc-skip-member` event.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application instance.
    """
    app.connect("autodoc-skip-member", skip_member)
