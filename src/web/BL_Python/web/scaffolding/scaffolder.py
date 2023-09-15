import logging
from argparse import ArgumentParser, Namespace
from dataclasses import asdict, dataclass
from os import environ
from pathlib import Path
from typing import Any, cast

from jinja2 import BaseLoader, Environment, PackageLoader, Template


@dataclass
class ScaffoldEndpoint:
    blueprint_name: str


@dataclass
class ScaffoldModules:
    database: bool = True


@dataclass
class ScaffoldConfig:
    template_type: str
    output_directory: str
    modules: ScaffoldModules | None
    endpoints: list[ScaffoldEndpoint] | None


class Scaffolder:
    def __init__(self, config: ScaffoldConfig, log: logging.Logger) -> None:
        self._config = config
        self._config_dict = asdict(config)
        self._log = log
        self._checked_directories: set[Path] = set()
        self._base_env = Environment(
            loader=BaseLoader  # pyright: ignore[reportGeneralTypeIssues]
        )

    def _create_directory(self, directory: Path):
        if directory in self._checked_directories:
            return

        self._checked_directories.add(directory)
        if directory.exists():
            self._log.warn(f"{directory} already exists. Files may be overwritten.")
        else:
            self._log.debug(f"Creating directory `{directory}`.")
            directory.mkdir(parents=True, exist_ok=True)

    def _render_template_string(
        self, template_string: str, template_config: dict[str, Any] | None = None
    ):
        if template_config is None:
            template_config = self._config_dict

        self._log.debug(
            f"Rendering template string `{template_string}` with config `{template_config}`."
        )

        rendered_string = self._base_env.from_string(template_string).render(
            **template_config
        )

        self._log.debug(
            f"Rendered template string `{template_string}` to `{rendered_string}`."
        )

        return rendered_string

    def _render_template(
        self,
        template_name: str,
        template_environment: Environment,
        template_config: dict[str, Any] | None = None,
        template: Template | None = None,
    ):
        if template_config is None:
            template_config = self._config_dict

        template_output_path = Path(
            self._config.output_directory, template_name.replace(".j2", "")
        )

        self._create_directory(template_output_path.parent)

        self._log.debug(
            f"Rendering template `{template_output_path}` with config `{template_config}`"
        )

        if not template:
            template = template_environment.get_template(template_name)

        template.stream(**template_config).dump(str(template_output_path))

    def _scaffold_base(self, env: Environment):
        # render the base templates
        for template_name in cast(list[str], env.list_templates()):
            self._render_template(template_name, env)

    def _scaffold_modules(self, env: Environment):
        if self._config.modules is None:
            self._log.debug("No optional modules to scaffold.")
            return

        # render optional module templates
        for module in asdict(self._config.modules):
            module_is_enabled = getattr(self._config.modules, module)
            if module_is_enabled:
                template = env.get_template(f"modules/{module}.py.j2")

                if template.name is None:
                    self._log.error(
                        f"Could not find template `modules/{module}.py.j2`."
                    )
                    continue

                self._render_template(template.name, env, template=template)

    def _scaffold_endpoints(self, env: Environment):
        # FIXME update config so endpoints cannot be none
        if self._config.endpoints is None:
            self._log.debug("No endpoints to scaffold.")
            return

        # render optional API endpoint templates
        for endpoint in [asdict(dc) for dc in self._config.endpoints]:
            # {{blueprint_name}} is the file name - this is _not_ meant to be an interpolated string
            template = env.get_template("blueprints/{{blueprint_name}}.py.j2")

            if template.name is None:
                self._log.error(
                    f"Could not find template `blueprints/{{blueprint_name}}.py.j2`."
                )
                continue

            rendered_template_name = self._render_template_string(
                template.name, endpoint
            )

            # make the current blueprint configuration available
            # in a top-level `blueprint` variable
            template_config = self._config_dict.copy()
            template_config["blueprint"] = endpoint

            self._render_template(
                rendered_template_name,
                env,
                template_config,
                template,
            )

    def scaffold(self):
        env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=PackageLoader(
                "BL_Python.web", f"scaffolding/templates/{self._config.template_type}"
            ),
        )
        optional_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=PackageLoader("BL_Python.web", f"scaffolding/templates/optional"),
        )

        self._scaffold_base(env)
        self._scaffold_modules(optional_env)
        self._scaffold_endpoints(optional_env)
