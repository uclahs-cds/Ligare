import logging
import sys
import types
from dataclasses import asdict, dataclass, field
from importlib.machinery import SourceFileLoader
from importlib.metadata import PackageNotFoundError
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, cast

from BL_Python.programming.collections.dict import merge
from jinja2 import BaseLoader, Environment, PackageLoader, Template
# fmt: off
from pkg_resources import \
    ResourceManager  # pyright: ignore[reportUnknownVariableType,reportGeneralTypeIssues]
from pkg_resources import get_provider

# fmt: on


@dataclass
class ScaffoldEndpoint:
    endpoint_name: str
    # This is Flask's default hostname.
    hostname: str = "http://127.0.0.1:5000"


@dataclass
class ScaffoldModule:
    module_name: str


@dataclass
class ScaffoldConfig:
    output_directory: str
    application_name: str
    template_type: str | None = None
    modules: list[ScaffoldModule] | None = None
    module: dict[str, Any] = field(default_factory=dict)
    endpoints: list[ScaffoldEndpoint] | None = None
    mode: str = "create"


class Scaffolder:
    def __init__(self, config: ScaffoldConfig, log: logging.Logger) -> None:
        self._config = config
        self._config_dict = asdict(config)
        self._log = log
        self._checked_directories: set[Path] = set()
        # BaseLoader is used for rendering strings only. It does not need additional functionality.
        self._base_env = Environment(
            loader=BaseLoader  # pyright: ignore[reportGeneralTypeIssues]
        )

    def _create_directory(self, directory: Path, overwrite_existing_files: bool = True):
        """Create the directories that the rendered templates will be stored in."""
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
        """Render a string that may contain jinja2 directives."""
        if template_config is None:
            template_config = self._config_dict

        self._log.debug(
            f"Rendering template string `{template_string}` with config `{template_config}`."
        )

        rendered_string = self._base_env.from_string(
            template_string
        ).render(  # pyright: ignore[reportUnknownMemberType]
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
        template_directory_prefix: str = "",
        template_config: dict[str, Any] | None = None,
        template: Template | None = None,
        overwrite_existing_files: bool = True,
    ):
        """
        Render a template that can either be found by name in
        the provided `template_environment`, or render the provided `template`.

        :param template_name: The name of the template that might be discoverable in the `template_environment`.
        :param template_environment: The jinja2 template environment used for rendering the template.
        :param template_directory_prefix: If not provided, templates will be stored relative to their discovered root in the template environment.
            For example, if the discovered template relative to the template environment exists at `./__init__.py`, the rendered template will be
            stored at `<output directory>/__init__.py`. If the template environment root points to a deeper directory in the template hierarchy,
            for example, in `{{application_name}}/modules/database/`, and the rendered template is `./__init__.py`, this default behavior
            is undesired. To resolve this, `template_directory_prefix` can be set in order to cause the rendered template to be stored under a
            different directory. For example, with the `template_directory_prefix` of `optional/{{application_name}}/modules/database/`, if the
            file `./__init__.py` is discovered at the template environment root,
            the file will instead be stored at `<output directory>/{{application_name}}/modules/database/__init__.py`.
        :param template_config: A dictionary of values that the template can reference.
        :param template: If provided, this template will be rendered instead of trying to discover the template with the name `template_name`
            in the template environment.
        :param overwrite_existing_files: If True, any existing files will be overwritten. If False, the template will not be rendered, and
            the file at the output location will not be overwritten.
        """
        if template_config is None:
            template_config = self._config_dict

        template_output_path = Path(
            self._config.output_directory,
            template_directory_prefix,
            # This causes paths with jinja2 directives to be rendered.
            # For example, if `self._config_dict['application_name']` is `foo`,
            # the path `base/{{application_name}}` is rendered as `base/foo`.
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

        # if a template is not provided, find the template in the environment
        if not template:
            template = template_environment.get_template(template_name)

        template.stream(  # pyright: ignore[reportUnknownMemberType]
            **template_config
        ).dump(str(template_output_path))

    def _scaffold_directory(
        self,
        env: Environment,
        template_directory_prefix: str = "",
        overwrite_existing_files: bool = True,
    ):
        """
        Render all templates discovered under the root directory of the provided template environment.
        Rendered templates are output relative to their location in the template directory, prefixed
        with `<output directory>/template_directory_prefix`.
        Only files ending with `.j2` are rendered.
        """
        # render the base templates
        for template_name in cast(
            list[str],
            env.list_templates(  # pyright: ignore[reportUnknownMemberType]
                extensions=["j2"]
            ),
        ):
            self._render_template(
                template_name,
                env,
                template_directory_prefix=template_directory_prefix,
                overwrite_existing_files=overwrite_existing_files,
            )

    # These are used to aid in discovering files that are
    # part of the BL_Python.web module. Relative path lookups
    # do not work, so they are done using _provider.
    _manager: Any = ResourceManager()
    _provider = get_provider("BL_Python.web")

    def _execute_module_hooks(self, module_template_directory: str):
        """
        Modules may have a file named `__hook__.py`. If it exists, it
        is executed as part of the scaffolding process.

        Hooks that can be configured in a module are:
            Called when an application is being created:
            `on_create(config: dict[str, Any], log: Logger) -> None`
        """
        module_hook_path = Path(module_template_directory, "__hook__.py")
        if self._provider.has_resource(  # pyright: ignore[reportUnknownMemberType]
            str(module_hook_path)
        ):
            # load the module from its path
            # and execute it
            spec = spec_from_file_location(
                "__hook__",
                self._provider.get_resource_filename(  # pyright: ignore[reportUnknownArgumentType,reportUnknownMemberType]
                    self._manager, str(module_hook_path)
                ),
            )
            if spec is None or spec.loader is None:
                raise Exception(
                    f"Module cannot be created from path {module_hook_path}"
                )
            module = module_from_spec(spec)
            spec.loader.exec_module(module)

            for module_name, module_var in vars(module).items():
                if not module_name.startswith("on_"):
                    continue
                # Execute methods starting with `on_`.
                # Since `_execute_module_hooks` is currently
                # only called when an application is being created,
                # any such method is only called when an application
                # is being created. Although the only documented
                # method allowed is `on_create`, any such prefixed
                # method will be called.
                module_var(self._config_dict, self._log)

    def _scaffold_modules(self, overwrite_existing_files: bool = True):
        """
        Render any modules configured to render.
        """
        if self._config.modules is None:
            self._log.debug("No optional modules to scaffold.")
            return

        # each module's configuration currently only includes
        # the module's name. This name also matches the filesystem
        # directory for the module's templates.
        for module in self._config.modules:
            # module templates are stored under `optional/`
            # because we don't always want to render any given module.
            module_template_directory = f"scaffolding/templates/optional/{{{{application_name}}}}/modules/{module.module_name}"
            # executed module hooks before any rendering is done
            # so the hooks can modify the config or do other
            # work if it's needed.
            self._execute_module_hooks(module_template_directory)

            module_env = Environment(
                trim_blocks=True,
                lstrip_blocks=True,
                loader=PackageLoader("BL_Python.web", str(module_template_directory)),
            )

            self._scaffold_directory(
                module_env,
                # prefix the directory so that rendered templates
                # are output _not_ relative to the template environment
                # root, which would store the rendered templates in `./`.
                template_directory_prefix=f"{self._config.application_name}/modules/{module.module_name}",
                overwrite_existing_files=overwrite_existing_files,
            )

    def _scaffold_endpoints(
        self, env: Environment, overwrite_existing_files: bool = True
    ):
        """
        Render API endpoint templates.
        """
        # technically, `self._config.endpoints` is always set in `__main__`
        # but we do this check to satisfy the type checker.
        if self._config.endpoints is None:
            self._log.debug("No endpoints to scaffold.")
            return

        # render optional API endpoint templates.
        # these templates are stored under `optional/` because:
        # 1. they are functionally optional. an application can be
        #    scaffolded without any endpoints, although `__main__` forces
        #    at least one endpoint.
        # 2. more than one endpoint can be rendered, so a location
        #    for the templates that is not used to render an entire
        #    directory of templates (like the `base` templates) is needed.
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

            template_string_config = merge(self._config_dict.copy(), endpoint)

            # render the template output path, replacing the jinja2
            # directives with their associated values from `self._config_dict`.
            rendered_template_name = self._render_template_string(
                template.name, template_string_config
            )

            self._log.info(
                f"\"{endpoint['endpoint_name']}\" will be accessible at {endpoint['hostname']}/{endpoint['endpoint_name']}"
            )

            # make the current endpoint configuration available
            # in a top-level `endpoint` variable
            template_config = self._config_dict.copy()
            template_config["endpoint"] = endpoint

            self._render_template(
                rendered_template_name,
                env,
                template_config=template_config,
                template=template,
                overwrite_existing_files=overwrite_existing_files,
            )

    # it is safe for create if:
    #      - the <application name> directory does not exist
    #      - if it does, that the directory does not contain an application
    # it is safe for modify if:
    #      - the <application name> directory exists
    #      - the scaffolder is run from the application parent directory
    #          - meaning the <application name> directory contains some kind of fingerprint
    def _check_scaffolded_application_exists(self):
        """Test that the scaffolder is running from a safe directory to ensure it runs as expected."""
        if self._config.mode == "create":
            sys.path.insert(0, str(Path(".", self._config.output_directory)))

            try:
                # if any of these steps fail, then the output directory
                # does not already contain a scaffolded application
                loader = SourceFileLoader(
                    self._config.application_name,
                    str(
                        Path(
                            self._config.output_directory,
                            self._config.application_name,
                            "__init__.py",
                        )
                    ),
                )
                mod = types.ModuleType(loader.name)
                sys.modules[self._config.application_name] = mod
                module = loader.load_module()
                breakpoint()
                _ = module.__version__
                _ = module._version.__bl_python_scaffold__
                # if no errors occur, then the output directory
                # contains a scaffolded application
                return True
            except Exception:
                return False
            finally:
                _ = sys.path.pop(0)

    def scaffold(self):
        print(self._check_scaffolded_application_exists())
        # print("SAFETY CHECK")
        # if self._config.mode == "create":
        #    pass
        ## other mode is "modify"
        # else:
        #    if not self._check_can_safely_run():
        #        self._log.critical(
        #            f"You are not running the scaffolder from an existing application parent directory."
        #        )
        #        return

        # used for the primary set of templates that a
        # scaffolded application is made up of.
        base_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=PackageLoader("BL_Python.web", f"scaffolding/templates/base"),
        )
        # used for the selected template type templates
        # that can replace files from the base templates.
        template_type_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=PackageLoader(
                "BL_Python.web", f"scaffolding/templates/{self._config.template_type}"
            ),
        )
        # used for templates under `optional/`
        optional_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=PackageLoader("BL_Python.web", f"scaffolding/templates/optional"),
        )

        if self._config.mode == "create":
            # scaffold modules first so they can alter the config if necessary.
            # a template environment is not passed in because `scaffold_modules`
            # creates a new environment for each module.
            self._scaffold_modules()

            self._scaffold_directory(base_env)
            # template type should go after base so it can override any base templates.
            self._scaffold_directory(template_type_env)

            self._scaffold_endpoints(optional_env)
        # other mode is "modify"
        else:
            # currently only endpoints can be modified through
            # this tool, and they can only be added.
            self._scaffold_endpoints(optional_env, overwrite_existing_files=False)
