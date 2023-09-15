import logging
from argparse import ArgumentParser
from os import environ
from pathlib import Path

from BL_Python.web.scaffolding import (
    ScaffoldConfig,
    ScaffoldEndpoint,
    Scaffolder,
    ScaffoldModules,
)

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
        help="An optional module to include in the application. Can be specified more than once.",
    )
    _ = parser.add_argument(
        "-e",
        action="append",
        metavar="endpoint",
        dest="endpoints",
        type=str,
        help="The name of an endpoint to scaffold. Can be specified more than once. If not specified, an endpoint sharing the name of the application will be scaffolded.",
    )

    args = parser.parse_args()

    if args.output_directory is None:
        args.output_directory = args.name

    if args.endpoints is None:
        args.endpoints = [args.name]

    return args


def scaffold():
    args = parse_args()

    print(
        f"Scaffolding {args.template_type} template named {args.name} under directory {Path(args.output_directory).absolute()}"
    )

    template_config = ScaffoldConfig(
        template_type=args.template_type,
        output_directory=args.output_directory,
        modules=ScaffoldModules(),
        endpoints=[ScaffoldEndpoint(blueprint_name="testfoobar")],
    )

    scaffolder = Scaffolder(template_config, log)
    scaffolder.scaffold()
