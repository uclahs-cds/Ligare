#!/usr/bin/env python3

import argparse
import importlib.util
import re
import sys
from argparse import Namespace
from glob import glob
from os import environ, linesep
from pathlib import Path
from sys import exit
from typing import Any

import toml

# Import Ligare.programming.cli.argparse.
# This must be done this way as this script is not used within an
# environment in which Ligare has been installed, and so
# the modules cannot be imported the usual way.
programming_module_name = "Ligare.programming.cli.argparse"
module_path = Path(
    Path(__file__).parent,
    "../../../src/programming/Ligare/programming/cli/argparse.py",
)
spec = importlib.util.spec_from_file_location(programming_module_name, str(module_path))
if spec is None or not spec.loader:
    raise Exception(f"Could not find module `{programming_module_name}`.")
Ligare_argparse = importlib.util.module_from_spec(spec)
sys.modules[programming_module_name] = Ligare_argparse
spec.loader.exec_module(Ligare_argparse)
# finish import


class RewriteArgs(Namespace):
    config: list[Path] | None = None


parser = argparse.ArgumentParser(
    description="""
This script accepts the following environment variables:
    - REWRITE_DEPENDENCIES: If true, this script will rewrite dependencies in pyproject.toml files.
        Otherwise, the script exits.
    - GITHUB_REF: The Git or GitHub ref triggering the script from a GitHub Action.
        If this starts with `refs/tags` or is not set, the script exits.
    - GITHUB_WORKSPACE: The directory the script is running within.
        If not set, the script exits.
"""
)
_ = parser.add_argument(
    "-c",
    "--config",
    type=Path,
    action=Ligare_argparse.PathExists,
    help="The path to the pyproject.toml file to rewrite. If not specified, all pyproject.toml under src/*/pyproject.toml, and pyproject.toml will be processed.",
    required=False,
)
args = parser.parse_args(namespace=RewriteArgs)

LIGARE = "Ligare"
WORKFLOW_DISPATCH_REWRITE_DEPENDENCIES = environ.get("REWRITE_DEPENDENCIES") or "true"
GIT_REF = environ.get("GITHUB_REF")

if (
    # Use the dependencies committed to the repository's
    # pyproject.toml files _without_ changing them
    # to use the local filesystem references.
    # Do this when:
    #   - The workflow explicitly says not to change dependencies
    #   - There is no specified GitHub Actions Git ref
    #   - The event was triggered by a Git tag
    # All other commits should use the local filesystem
    # in order to test against the current state of the repository.
    WORKFLOW_DISPATCH_REWRITE_DEPENDENCIES.lower() == "false"
    or GIT_REF is None
    or GIT_REF.startswith("refs/tags")
):
    print(
        f"""Not rewriting dependencies:{linesep}
  - REWRITE_DEPENDENCIES: '{WORKFLOW_DISPATCH_REWRITE_DEPENDENCIES}'{linesep}
  - GIT_REF: '{GIT_REF}'"""
    )
    exit(0)

WORKDIR = environ.get("GITHUB_WORKSPACE")
if WORKDIR is None:
    raise ValueError("GITHUB_WORKSPACE is not set.")


pyproject_files: list[str]
if args.config:
    pyproject_files = [str(Path(WORKDIR, path)) for path in args.config]
else:
    pyproject_files = [str(Path(WORKDIR, "pyproject.toml"))] + glob(
        str(Path(WORKDIR, "src/*/pyproject.toml"))
    )

for pyproject_file in pyproject_files:
    print(
        f"Rewriting Ligare dependency specifications in {pyproject_file} for filesystem build."
    )

    data: dict[str, Any]
    with open(pyproject_file, "r") as f:
        data = toml.load(f)

    dependencies: list[str] = data["project"]["dependencies"]
    dependencies_hash = hash(tuple(dependencies))

    for idx, dependency in enumerate(dependencies):
        if not dependency.startswith(LIGARE):
            continue

        dependency_match = re.match(r"(Ligare\.[^=<!~\s]+)", dependency)
        if dependency_match is None:
            raise ValueError(f"Ligare dependency name '{dependency}' is invalid.")

        dependency = dependency_match[0]

        # e.g. "web" in "Ligare.web"
        sub_dep = dependency[dependency.index(".") + 1 :]
        dep_path = WORKDIR + (
            f"/{sub_dep}" if dependency == LIGARE else f"/src/{sub_dep}"
        )
        new_dep = f"{dependency} @ file://{dep_path}"
        dependencies[idx] = new_dep

    # list has not changed?
    if dependencies_hash == hash(tuple(dependencies)):
        print(f"Skipped writing {pyproject_file}. No Ligare dependencies in file.")
        continue

    with open(pyproject_file, "w") as f:
        new_pyproject = toml.dump(data, f)
        print(f"New {pyproject_file} contents:{linesep*2}{new_pyproject}")
