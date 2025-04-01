#!/usr/bin/env python3

import argparse
import glob
import importlib.util
from glob import glob
from os import environ, getcwd
from pathlib import Path
from typing import Any, cast

# https://stackoverflow.com/a/79380110
try:
    import tomllib  # pyright: ignore[reportMissingImports] exists in Python 3.11+
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib  # the same tomllib that's now included in Python v3.11+


# https://stackoverflow.com/a/70859914
def closest_file(start: Path, filename: str) -> None | Path:
    if start == Path(start.root) or start == start.parent:
        return None

    fullpath = Path(start, filename)
    return fullpath if fullpath.exists() else closest_file(start.parent, filename)


def get_project_name(path: Path) -> str | None:
    with open(path, "rb") as f:
        data = cast(dict[Any, Any], tomllib.load(f))  # pyright: ignore[reportPrivateImportUsage, reportUnknownMemberType]
        return data.get("project", {}).get("name", None)


def get_working_directory() -> Path | None:
    if (working_dir := environ.get("GITHUB_WORKSPACE", None)) is not None:
        return Path(working_dir)

    GITHUB_WORKFLOWS_PATH = ".github/workflows"
    cwd = getcwd()
    if GITHUB_WORKFLOWS_PATH in getcwd():
        return Path(cwd[: cwd.index(GITHUB_WORKFLOWS_PATH)])

    def walk_tree(start: Path | None) -> Path | None:
        if start is None:
            return None

        closest_pyproject_file = closest_file(start, "pyproject.toml")
        if closest_pyproject_file is None:
            return None

        project_name = get_project_name(closest_pyproject_file)
        if project_name is None:
            return None

        if project_name == "Ligare.all":
            return closest_pyproject_file.parent

        return walk_tree(closest_pyproject_file.parent.parent)

    return walk_tree(Path(cwd))


def get_module_version(module_name: str):
    working_directory = get_working_directory()

    if working_directory is None:
        raise Exception("Unable to determine location of Ligare source code.")

    module_path_name = module_name.split(".")[1]
    module_path = Path(
        working_directory,
        "src",
        module_path_name,
        "Ligare",
        module_path_name,
        "__init__.py",
    )
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or not spec.loader:
        raise Exception(f"Could not find module `{module_name}`.")
    ligare_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ligare_module)
    return ligare_module.__version__


def find_ligare_modules() -> list[str]:
    working_directory = get_working_directory()
    if working_directory is None:
        raise Exception("Unable to determine location of Ligare source code.")

    # the length of "/__init__.py"
    INIT_NAME_LEN = 12

    module_paths = glob(str(Path(working_directory, "src/*/Ligare/*/__init__.py")))

    return [
        # turn `f"{working_directory}src/platform/Ligare/platform/__init__.py"`` into `"Ligare.platform"``
        module_path[module_path.rindex("Ligare") : -INIT_NAME_LEN].replace("/", ".")
        for module_path in module_paths
    ]


def main():
    parser = argparse.ArgumentParser(
        "GetModuleVersion", "Get the version of a Ligare module."
    )
    original_error = parser.error

    def error(message: str):
        # Show the full help when required arguments aren't supplied
        parser.print_help()
        original_error(message)

    parser.error = error
    _ = parser.add_argument(
        "-m",
        metavar="modulename",
        dest="modulename",
        required=True,
        choices=find_ligare_modules(),
        help="Choose from: %(choices)s",
    )

    args = parser.parse_args()

    print(get_module_version(args.modulename), end="")


if __name__ == "__main__":
    main()
