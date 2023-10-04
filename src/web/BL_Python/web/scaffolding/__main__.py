import logging
from argparse import ArgumentParser, Namespace
from functools import partial
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
        level=int(environ.get("LOG_LEVEL")),  # pyright: ignore[reportGeneralTypeIssues]
        format="[%(levelname)-7s]: %(message)s",
    )
else:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)-7s] %(message)s")

log = logging.getLogger()


def _parse_args():
    parser = ArgumentParser(description="BL_Python Web Project Scaffolding Tool")

    subparsers = parser.add_subparsers(help="Select mode", required=True)

    create_parser = subparsers.add_parser(
        "create", help="Create a new BL_Python web application"
    )
    _ = create_parser.add_argument(
        "-n",
        metavar="name",
        dest="name",
        required=True,
        type=str,
        help="The name of the application.",
    )
    _ = create_parser.add_argument(
        "-e",
        action="append",
        metavar="endpoint",
        dest="endpoints",
        type=str,
        help="The name of an endpoint to scaffold. Can be specified more than once. If not specified, an endpoint sharing the name of the application will be scaffolded.",
    )
    template_types = ["basic", "openapi"]
    _ = create_parser.add_argument(
        "-t",
        choices=template_types,
        dest="template_type",
        type=str,
        default="basic",
        help="The type of template to scaffold.",
    )
    modules = ["database"]
    _ = create_parser.add_argument(
        "-m",
        choices=modules,
        action="append",
        dest="modules",
        type=str,
        help="An optional module to include in the application. Can be specified more than once.",
    )
    _ = create_parser.add_argument(
        "-o",
        metavar="output directory",
        dest="output_directory",
        type=str,
        help="The output directory. The default is a new directory sharing the name of the application.",
    )
    create_parser.set_defaults(mode_executor=partial(_run_create_mode), mode="create")

    modify_parser = subparsers.add_parser(
        "modify", help="Modify an existing BL_Python web application"
    )
    _ = modify_parser.add_argument(
        "-n",
        metavar="name",
        dest="name",
        required=True,
        type=str,
        help="The name of the application.",
    )
    _ = modify_parser.add_argument(
        "-e",
        action="append",
        metavar="endpoint",
        dest="endpoints",
        type=str,
        help="The name of an endpoint to scaffold. Can be specified more than once. If not specified, an endpoint sharing the name of the application will be scaffolded.",
    )
    _ = modify_parser.add_argument(
        "-o",
        metavar="output directory",
        dest="output_directory",
        type=str,
        help="The output directory. The default is a directory sharing the name of the application.",
    )
    modify_parser.set_defaults(mode_executor=partial(_run_modify_mode), mode="modify")

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


def _run_create_mode(args: Namespace):
    log.info("Running create mode.")

    log.info(
        f'Creating new application "{args.name}" from {args.template_type} template ...'
    )

    # TODO consider pulling licenses from GitHub
    # https://docs.github.com/en/rest/licenses/licenses?apiVersion=2022-11-28#get-all-commonly-used-licenses
    # https://docs.github.com/en/rest/licenses/licenses?apiVersion=2022-11-28#get-a-license
    config = ScaffoldConfig(
        mode=args.mode,
        template_type=args.template_type,
        output_directory=args.output_directory,
        application_name=args.name,
        modules=(
            []
            if args.modules is None
            else [ScaffoldModule(module_name=module) for module in args.modules]
        ),
        endpoints=[
            ScaffoldEndpoint(endpoint_name=endpoint) for endpoint in args.endpoints
        ],
    )

    scaffolder = Scaffolder(config, log)
    scaffolder.scaffold()


def _run_modify_mode(args: Namespace):
    log.info("Running modify mode.")

    config = ScaffoldConfig(
        mode=args.mode,
        output_directory=args.output_directory,
        application_name=args.name,
        endpoints=[
            ScaffoldEndpoint(endpoint_name=endpoint) for endpoint in args.endpoints
        ],
    )

    scaffolder = Scaffolder(config, log)
    scaffolder.scaffold()


def scaffold():
    args = _parse_args()

    print(
        f'Scaffolding application named "{args.name}" under directory `{Path(args.output_directory).absolute()}`.'
    )

    args.mode_executor(args)

    print("Done.")
