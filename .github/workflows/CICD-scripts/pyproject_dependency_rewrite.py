#!/usr/bin/env python3

import re
from glob import glob
from os import environ, linesep
from pathlib import Path
from sys import exit
from typing import Any

import toml

BL_PYTHON = "BL_Python"
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

pyproject_files = [str(Path(WORKDIR, "pyproject.toml"))] + glob(
    str(Path(WORKDIR, "src/*/pyproject.toml"))
)

for pyproject_file in pyproject_files:
    print(
        f"Rewriting BL_Python dependency specifications in {pyproject_file} for filesystem build."
    )

    data: dict[str, Any]
    with open(pyproject_file, "r") as f:
        data = toml.load(f)

    dependencies: list[str] = data["project"]["dependencies"]
    dependencies_hash = hash(tuple(dependencies))

    for idx, dependency in enumerate(dependencies):
        if not dependency.startswith(BL_PYTHON):
            continue

        dependency_match = re.match(r"(BL_Python\.[^=<!~\s]+)", dependency)
        if dependency_match is None:
            raise ValueError(f"BL_Python dependency name '{dependency}' is invalid.")

        dependency = dependency_match[0]

        # e.g. "web" in "BL_Python.web"
        sub_dep = dependency[dependency.index(".") + 1 :]
        dep_path = WORKDIR + (
            f"/{sub_dep}" if dependency == BL_PYTHON else f"/src/{sub_dep}"
        )
        new_dep = f"{dependency} @ file://{dep_path}"
        dependencies[idx] = new_dep

    # list has not changed?
    if dependencies_hash == hash(tuple(dependencies)):
        print(f"Skipped writing {pyproject_file}. No BL_Python dependencies in file.")
        continue

    with open(pyproject_file, "w") as f:
        new_pyproject = toml.dump(data, f)
        print(f"New {pyproject_file} contents:{linesep*2}{new_pyproject}")
