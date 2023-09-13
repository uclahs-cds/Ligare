import logging
from argparse import ArgumentParser, Namespace
from os import environ
from typing import cast

from jinja2 import nodes
from jinja2.ext import Extension

if environ.get("LOG_LEVEL"):
    logging.basicConfig(
        level=int(environ.get("LOG_LEVEL"))  # pyright: ignore[reportGeneralTypeIssues]
    )

log = logging.getLogger()


def parse_args():
    parser = ArgumentParser(description="BL_Python Web Project Scaffolding Tool")
    _ = parser.add_argument(
        "-n",
        metavar="name",
        dest="name",
        required=True,
        type=str,
        help="The name of the application.",
    )
    _ = parser.add_argument(
        "-o",
        metavar="output directory",
        dest="output_directory",
        type=str,
        help="The output directory. The default is a new directory sharing the name of the application.",
    )
    template_types = ["basic", "openapi"]
    _ = parser.add_argument(
        "-t",
        choices=template_types,
        dest="template_type",
        type=str,
        default="basic",
        help="The type of template to scaffold.",
    )
    modules = ["database"]
    _ = parser.add_argument(
        "-m",
        choices=modules,
        action="append",
        dest="modules",
        type=str,
        help="Optional modules to include in the application.",
    )

    args = parser.parse_args()

    if args.output_directory is None:
        args.output_directory = args.name

    return args


from dataclasses import dataclass


@dataclass
class ScaffoldModules:
    database = False


@dataclass
class ScaffoldConfig:
    modules: ScaffoldModules


from pathlib import Path

from jinja2 import Environment, PackageLoader


def scaffold_template(args: Namespace):
    template_type: str = args.template_type

    checked_directories: set[Path] = set()

    def create_directory(directory: Path):
        if directory not in checked_directories:
            checked_directories.add(directory)
            if directory.exists():
                log.warn(f"{directory} already exists. Files may be overwritten.")
            else:
                log.debug(f"Creating directory `{directory}`.")
                directory.mkdir(parents=True, exist_ok=True)
        pass

    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=PackageLoader("BL_Python.web", f"scaffolding/templates/{template_type}"),
    )

    should_skip = False

    # the use of this prevent parallelizing template rendering
    def skip_file(skip: bool):
        nonlocal should_skip
        should_skip = skip
        return

    env.globals["skip_file"] = skip_file

    template_config = ScaffoldConfig(modules=ScaffoldModules())
    # a list of directories already checked for existence
    for template_name in cast(list[str], env.list_templates()):
        should_skip = False
        template_output_path = Path(
            args.output_directory, template_name.replace(".j2", "")
        )

        create_directory(template_output_path.parent)

        log.debug(
            f"Rendering template `{template_output_path}`. Using config `{template_config}`"
        )
        r = env.get_template(template_name).render(**template_config.__dict__)
        # stream = env.get_template(template_name).stream(**template_config.__dict__)
        if not should_skip:
            with open(template_output_path, "w") as f:
                f.write(r)
            # stream.dump(str(template_output_path))


def scaffold():
    args = parse_args()

    print(
        f"Scaffolding {args.template_type} template named {args.name} under directory {Path(args.output_directory).absolute()}"
    )
    scaffold_template(args)
