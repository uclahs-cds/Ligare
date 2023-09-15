import logging
from argparse import ArgumentParser
from os import environ
from pathlib import Path

from BL_Python.web.scaffolding import (
    ScaffoldConfig,
    ScaffoldEndpoint,
    Scaffolder,
    ScaffoldModule,
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
    else:
        if "application" in args.endpoints:
            log.warn(
                'The endpoint name "application" is reserved and will not be scaffolded.'
            )
            args.endpoints.remove("application")

    return args


def scaffold():
    args = parse_args()

    print(
        f"Scaffolding {args.template_type} template named {args.name} under directory {Path(args.output_directory).absolute()}"
    )

    # TODO consider pulling licenses from GitHub
    # https://docs.github.com/en/rest/licenses/licenses?apiVersion=2022-11-28#get-all-commonly-used-licenses
    # https://docs.github.com/en/rest/licenses/licenses?apiVersion=2022-11-28#get-a-license

    template_config = ScaffoldConfig(
        template_type=args.template_type,
        output_directory=args.output_directory,
        application_name=args.name,
        modules=(
            None
            if args.modules is None
            else [ScaffoldModule(module_name=module) for module in args.modules]
        ),
        endpoints=[
            ScaffoldEndpoint(endpoint_name=endpoint) for endpoint in args.endpoints
        ],
    )

    scaffolder = Scaffolder(template_config, log)
    scaffolder.scaffold()
