import logging
from argparse import ArgumentParser, Namespace
from os import environ
from typing import Any, cast

from jinja2 import BaseLoader, Template

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


from dataclasses import asdict, dataclass


@dataclass
class ScaffoldEndpoint:
    blueprint_name: str


@dataclass
class ScaffoldModules:
    database: bool = True


@dataclass
class ScaffoldConfig:
    modules: ScaffoldModules | None
    endpoints: list[ScaffoldEndpoint] | None


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

    def get_templated_string(template_string: str, config: dict[str, Any]):
        return (
            Environment(loader=BaseLoader).from_string(template_string).render(**config)
        )

    def render_template(
        template_name: str,
        output_directory: str,
        template_environment: Environment,
        template_config: dict[str, Any],
        template: Template | None = None,
    ):
        template_output_path = Path(output_directory, template_name.replace(".j2", ""))

        create_directory(template_output_path.parent)

        log.debug(
            f"Rendering template `{template_output_path}`. Using config `{template_config}`"
        )

        if not template:
            template = template_environment.get_template(template_name)

        template.stream(**template_config).dump(str(template_output_path))

    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=PackageLoader("BL_Python.web", f"scaffolding/templates/{template_type}"),
    )
    optional_env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=PackageLoader("BL_Python.web", f"scaffolding/templates/optional"),
    )

    template_config = ScaffoldConfig(
        modules=ScaffoldModules(),
        endpoints=[ScaffoldEndpoint(blueprint_name="testfoobar")],
    )
    template_config_dict = asdict(template_config)

    # render the base templates
    for template_name in cast(list[str], env.list_templates()):
        render_template(template_name, args.output_directory, env, template_config_dict)

    # render optional module templates
    for module in asdict(template_config.modules):
        module_is_enabled = getattr(template_config.modules, module)
        if module_is_enabled:
            template = optional_env.get_template(f"modules/{module}.py.j2")

            if template.name is None:
                log.error(f"Could not find template `modules/{module}.py.j2`.")
                continue

            render_template(
                template.name,
                args.output_directory,
                optional_env,
                template_config_dict,
                template,
            )

    # render optional API endpoint templates
    for endpoint in [asdict(dc) for dc in template_config.endpoints]:
        template = optional_env.get_template("blueprints/{{blueprint_name}}.py.j2")

        if template.name is None:
            log.error(f"Could not find template `blueprints/{{blueprint_name}}.py.j2`.")
            continue

        rendered_template_name = get_templated_string(template.name, endpoint)

        # make the current blueprint configuration available
        # in a top-level `blueprint` variable
        template_config_copy = template_config_dict.copy()
        template_config_copy["blueprint"] = endpoint

        render_template(
            rendered_template_name,
            args.output_directory,
            optional_env,
            template_config_copy,
            template,
        )


def scaffold():
    args = parse_args()

    print(
        f"Scaffolding {args.template_type} template named {args.name} under directory {Path(args.output_directory).absolute()}"
    )

    scaffold_template(args)
