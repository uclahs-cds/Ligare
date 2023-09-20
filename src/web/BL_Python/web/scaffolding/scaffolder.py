import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

from BL_Python.programming.collections.dict import merge
from jinja2 import BaseLoader, Environment, PackageLoader, Template


@dataclass
class ScaffoldEndpoint:
    endpoint_name: str


@dataclass
class ScaffoldModule:
    module_name: str


@dataclass
class ScaffoldConfig:
    output_directory: str
    application_name: str
    template_type: str | None = None
    modules: list[ScaffoldModule] | None = None
    endpoints: list[ScaffoldEndpoint] | None = None
    mode: str = "create"


class Scaffolder:
    def __init__(self, config: ScaffoldConfig, log: logging.Logger) -> None:
        self._config = config
        self._config_dict = asdict(config)
        self._log = log
        self._checked_directories: set[Path] = set()
        self._base_env = Environment(
            loader=BaseLoader  # pyright: ignore[reportGeneralTypeIssues]
        )

    def _create_directory(self, directory: Path, overwrite_existing_files: bool = True):
        if directory in self._checked_directories:
            return

        self._checked_directories.add(directory)
        if overwrite_existing_files and directory.exists():
            self._log.warn(f"Directory `{directory}` exists. Files may be overwritten.")
        else:
            self._log.debug(f"Creating directory `{directory}`.")
            # the "overwrite" check only applies in this method
            # to log a message. It is okay if a directory already exists.
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
        overwrite_existing_files: bool = True,
    ):
        if template_config is None:
            template_config = self._config_dict

        template_output_path = Path(
            self._config.output_directory,
            self._render_template_string(template_name).replace(".j2", ""),
        )

        if overwrite_existing_files == False and template_output_path.exists():
            self._log.warn(
                f"File `{template_output_path}` exists, but refusing to overwrite."
            )
            return

        self._create_directory(
            template_output_path.parent,
            overwrite_existing_files=overwrite_existing_files,
        )

        self._log.debug(
            f"Rendering template `{template_output_path}` with config `{template_config}`"
        )

        if not template:
            template = template_environment.get_template(template_name)

        template.stream(**template_config).dump(str(template_output_path))

    def _scaffold_directory(
        self, env: Environment, overwrite_existing_files: bool = True
    ):
        # render the base templates
        for template_name in cast(list[str], env.list_templates()):
            self._render_template(
                template_name, env, overwrite_existing_files=overwrite_existing_files
            )

    def _scaffold_modules(
        self, env: Environment, overwrite_existing_files: bool = True
    ):
        if self._config.modules is None:
            self._log.debug("No optional modules to scaffold.")
            return

        # render optional module templates
        for module in self._config.modules:
            template = env.get_template(
                f"{{{{application_name}}}}/modules/{module.module_name}.py.j2"
            )

            if template.name is None:
                self._log.error(
                    f"Could not find template `{{{{application_name}}}}/modules/{module.module_name}.py.j2`."
                )
                continue

            self._render_template(
                template.name,
                env,
                template=template,
                overwrite_existing_files=overwrite_existing_files,
            )

    def _scaffold_endpoints(
        self, env: Environment, overwrite_existing_files: bool = True
    ):
        if self._config.endpoints is None:
            self._log.debug("No endpoints to scaffold.")
            return

        # render optional API endpoint templates
        for endpoint in [asdict(dc) for dc in self._config.endpoints]:
            # {{endpoint_name}} is the file name - this is _not_ meant to be an interpolated string
            template = env.get_template(
                "{{application_name}}/endpoints/{{endpoint_name}}.py.j2"
            )

            if template.name is None:
                self._log.error(
                    "Could not find template `{{application_name}}/endpoints/{{endpoint_name}}.py.j2`."
                )
                continue

            template_string_config = merge(self._config_dict, endpoint)

            rendered_template_name = self._render_template_string(
                template.name, template_string_config
            )

            # make the current endpoint configuration available
            # in a top-level `endpoint` variable
            template_config = self._config_dict.copy()
            template_config["endpoint"] = endpoint

            self._render_template(
                rendered_template_name,
                env,
                template_config,
                template,
                overwrite_existing_files=overwrite_existing_files,
            )

    def scaffold(self):
        base_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=PackageLoader("BL_Python.web", f"scaffolding/templates/base"),
        )
        template_type_env = Environment(
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

        if self._config.mode == "create":
            self._scaffold_directory(base_env)
            # template type should go after base so it can override any base templates
            self._scaffold_directory(template_type_env)
            self._scaffold_modules(optional_env)
            self._scaffold_endpoints(optional_env)
        # other mode is "modify"
        else:
            # currently only endpoints can be modified through
            # this tool, and they can only be added.
            self._scaffold_endpoints(optional_env, overwrite_existing_files=False)
