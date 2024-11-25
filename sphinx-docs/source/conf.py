# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from sphinx.application import Sphinx
from sphinx.ext.autodoc import Options

project = "Ligare"
copyright = "2024, Aaron Holmes"
author = "Aaron Holmes"

master_doc = "index"

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "sphinx_rtd_theme"
pygments_style = "one-dark"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

extensions = [
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx_autodoc_typehints",
    "sphinx_toolbox.more_autodoc.autoprotocol",
    "sphinx_copybutton",
    "sphinx.ext.viewcode",
    "sphinx.ext.extlinks",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": False,
    "special-members": "__init__,__new__,__version__",
}

autodoc_type_aliases = {
    "_typeshed": "Any",
    "_typeshed.ReadableBuffer": "Any",
    "ReadableBuffer": "Any",
}

copybutton_exclude = ".linenos, .gp"
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True

github_ref = os.environ.get("GITHUB_REF") or "main"

extlinks = {
    "source": (
        f"https://github.com/uclahs-cds/Ligare/blob/{github_ref}/%s",
        None,
    ),
    "example": (
        f"https://github.com/uclahs-cds/Ligare/blob/{github_ref}/examples/%s",
        "Review example sources [%s]",
    ),
    "archive": (
        "https://uclahs-cds.github.io/Ligare/_downloads/%s.zip",
        "Download example archive [%s.zip]",
    ),
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


def create_zips_for_examples(app: Sphinx, exception: Exception | None):
    if exception is not None:
        return

    examples_dir = Path("examples").resolve()
    example_paths = examples_dir.glob("*")
    output_dir = Path(app.outdir, "_downloads")

    if not output_dir.exists():
        output_dir.mkdir()

    for example_path in example_paths:
        # Store the zip file in the `_downloads` output directory with the name
        # of the example (which is the directory name), e.g. _downloads/web-api.zip
        with zipfile.ZipFile(
            Path(output_dir, f"{example_path.name}.zip"), "w", zipfile.ZIP_DEFLATED
        ) as zip_file:
            for root, _, files in os.walk(examples_dir):
                for file in files:
                    file_path = Path(root, file)
                    arcname = Path.relative_to(file_path, examples_dir)
                    zip_file.write(file_path, arcname)


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
    _ = app.connect("build-finished", create_zips_for_examples)
