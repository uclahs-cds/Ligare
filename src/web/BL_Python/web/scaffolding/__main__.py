import logging
import sys
from argparse import ArgumentParser, Namespace
from functools import partial
from os import environ
from pathlib import Path
from typing import Callable, Literal, NamedTuple

from BL_Python.programming.cli.argparse import (
    associate_disallow_duplicate_values,
    disallow,
)
from BL_Python.web.scaffolding import (
    Operation,
    ScaffoldConfig,
    ScaffoldEndpoint,
    Scaffolder,
    ScaffoldModule,
)
from typing_extensions import final

APPLICATION_ENDPOINT_PATH_NAME = "application"


class ScaffoldInputArgs(Namespace):
    mode: Literal[  # pyright: ignore[reportUninitializedInstanceVariable]
        "create", "modify"
    ]
    mode_executor: "Callable[[ScaffoldParsedArgs], None]"  # pyright: ignore[reportUninitializedInstanceVariable]
    name: Operation  # pyright: ignore[reportUninitializedInstanceVariable]
    endpoints: list[Operation] | None = None
    template_type: Literal["basic", "openapi"] = "basic"
    modules: list[Literal["database"]] | None = None
    output_directory: str | None = None


class ScaffoldParsedArgs(NamedTuple):
    mode: Literal["create", "modify"]
    mode_executor: "Callable[[ScaffoldParsedArgs], None]"
    name: Operation
    endpoints: list[Operation]
    template_type: Literal["basic", "openapi"]
    modules: list[Literal["database"]] | None
    output_directory: str


@final
class ScaffolderCli:
    _log: logging.Logger

    def __init__(self, log_level: int | str | None = None) -> None:
        _log_level = log_level
        if log_level is not None:
            # support both integer and named log level values
            # from the envvar, e.g., `10` or `DEBUG`
            try:
                _log_level = int(log_level)
            except ValueError as e:
                if not "invalid literal for int" in str(e):
                    raise
                _log_level = getattr(logging, str(log_level).upper())

        logging.basicConfig(
            level=_log_level if _log_level is not None else logging.INFO,
            format="[%(levelname)-7s] %(message)s",
        )

        self._log = logging.getLogger()

    def _parse_args(self, args: list[str]) -> ScaffoldParsedArgs:
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
            type=disallow([APPLICATION_ENDPOINT_PATH_NAME], "name", Operation),
            help="The name of the application.",
        )
        _ = create_parser.add_argument(
            "-e",
            metavar="endpoint",
            dest="endpoints",
            type=disallow([APPLICATION_ENDPOINT_PATH_NAME], "endpoint", Operation),
            action=associate_disallow_duplicate_values("name"),
            help="The name of an endpoint to scaffold. Can be specified more than once. If not specified, an endpoint sharing the name of the application will be scaffolded.",
        )
        template_types = ["basic", "openapi"]
        _ = create_parser.add_argument(
            "-t",
            choices=template_types,
            dest="template_type",
            type=str.lower,
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
        create_parser.set_defaults(
            mode_executor=partial(self._run_create_mode), mode="create"
        )

        modify_parser = subparsers.add_parser(
            "modify", help="Modify an existing BL_Python web application"
        )
        _ = modify_parser.add_argument(
            "-n",
            metavar="name",
            dest="name",
            required=True,
            type=disallow([APPLICATION_ENDPOINT_PATH_NAME], "name", Operation),
            help="The name of the application.",
        )
        _ = modify_parser.add_argument(
            "-e",
            metavar="endpoint",
            dest="endpoints",
            type=disallow([APPLICATION_ENDPOINT_PATH_NAME], "endpoint", Operation),
            action=associate_disallow_duplicate_values("name"),
            help="The name of an endpoint to scaffold. Can be specified more than once. If not specified, an endpoint sharing the name of the application will be scaffolded.",
        )
        _ = modify_parser.add_argument(
            "-o",
            metavar="output directory",
            dest="output_directory",
            type=str,
            help="The output directory. The default is a directory sharing the name of the application.",
        )
        modify_parser.set_defaults(
            mode_executor=partial(self._run_modify_mode), mode="modify"
        )

        _args = parser.parse_args(args, namespace=ScaffoldInputArgs)

        if _args.output_directory is None:
            _args.output_directory = _args.name.module_name

        if _args.endpoints is None:
            _args.endpoints = [_args.name]
        else:
            endpoints = {
                endpoint.url_path_name: endpoint for endpoint in _args.endpoints
            }
            if APPLICATION_ENDPOINT_PATH_NAME in endpoints:
                self._log.warn(
                    f'The endpoint name "{APPLICATION_ENDPOINT_PATH_NAME}" is reserved and will not be scaffolded.'
                )
                _args.endpoints.remove(endpoints[APPLICATION_ENDPOINT_PATH_NAME])

        return ScaffoldParsedArgs(
            _args.mode,
            _args.mode_executor,
            _args.name,
            _args.endpoints,
            _args.template_type,
            _args.modules,
            _args.output_directory,
        )

    def _run_create_mode(self, args: ScaffoldParsedArgs):
        self._log.info("Running create mode.")

        self._log.info(
            f'Creating new application "{args.name}" from {args.template_type} template ...'
        )

        # TODO consider pulling licenses from GitHub
        # https://docs.github.com/en/rest/licenses/licenses?apiVersion=2022-11-28#get-all-commonly-used-licenses
        # https://docs.github.com/en/rest/licenses/licenses?apiVersion=2022-11-28#get-a-license
        config = ScaffoldConfig(
            mode=args.mode,
            template_type=args.template_type,
            output_directory=args.output_directory,
            application=args.name,
            modules=(
                []
                if args.modules is None
                else [ScaffoldModule(module_name=module) for module in args.modules]
            ),
            endpoints=[
                ScaffoldEndpoint(operation=endpoint) for endpoint in args.endpoints
            ],
        )

        scaffolder = Scaffolder(config, self._log)
        scaffolder.scaffold()

    def _run_modify_mode(self, args: ScaffoldParsedArgs):
        self._log.info("Running modify mode.")

        config = ScaffoldConfig(
            mode=args.mode,
            output_directory=args.output_directory,
            application=args.name,
            endpoints=[
                ScaffoldEndpoint(operation=endpoint) for endpoint in args.endpoints
            ],
        )

        scaffolder = Scaffolder(config, self._log)
        scaffolder.scaffold()

    def run(self, argv: list[str]):
        args = self._parse_args(argv)

        print(
            f'Scaffolding application named "{args.name}" under directory `{Path(args.output_directory).absolute()}`.'
        )

        args.mode_executor(args)


def scaffold(argv: list[str] | None = None, log_level: int | str | None = None):
    if not log_level:
        log_level = environ.get("LOG_LEVEL")

    if not argv:
        argv = sys.argv[1:]

    cli = ScaffolderCli(log_level)
    cli.run(argv)
    print("Done.")
