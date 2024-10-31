# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from typing import Any
from unittest.mock import Mock

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

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

extensions = [
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_toolbox.more_autodoc.autoprotocol",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": False,
    "special-members": "__init__",
}

autodoc_type_aliases = {
    "_typeshed": "Any",
    "_typeshed.ReadableBuffer": "Any",  # or define as per your needs
    "ReadableBuffer": "Any",  # handles forward references
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


def replace_init_with_call(
    app: Sphinx, what: str, name: str, obj: Any, options: Any, lines: list[str]
) -> None:
    # If `__init__` is being documented on a Protocol, replace its docs with `__call__`
    if what == "class" and name == "__init__" and hasattr(obj, "__call__"):
        call_docs = (obj.__call__.__doc__ or "").splitlines()
        lines.clear()
        lines.extend(call_docs)


def setup(app: Sphinx) -> None:
    """
    Connects the `skip_member` function to the `autodoc-skip-member` event.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application instance.
    """
    # prevent
    # WARNING: Failed guarded type import with ModuleNotFoundError("No module named '_typeshed'")
    sys.modules["_typeshed"] = Mock()
    _ = app.connect("autodoc-skip-member", skip_member)
    _ = app.connect("autodoc-process-docstring", replace_init_with_call)
