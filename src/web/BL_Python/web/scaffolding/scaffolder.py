import logging
import re
import sys
import types
from dataclasses import asdict, dataclass, field
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from os import sep as path_separator
from pathlib import Path
from typing import Any, final

from BL_Python.programming.collections.dict import merge
from jinja2 import BaseLoader, Environment, PackageLoader, Template

# fmt: off
from pkg_resources import (
    ResourceManager,  # pyright: ignore[reportUnknownVariableType,reportAttributeAccessIssue]
)
from pkg_resources import get_provider
from typing_extensions import final, override

# fmt: on


@dataclass
class Operation:
    url_path_name: str
    module_name: str
    raw_name: str

    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self, name: str, **kwargs: Any | None
    ) -> None:
        name_lower = name.lower()
        self.raw_name = name
        self.url_path_name = name_lower
        self.module_name = re.sub(r"[^\w_]", "_", name_lower)

    @override
    def __str__(self) -> str:
        return self.url_path_name

    @override
    def __eq__(self, __value: object) -> bool:

        return isinstance(__value, Operation) and (
            self.url_path_name == __value.url_path_name
            or self.module_name == __value.module_name
        )


@dataclass
class ScaffoldEndpoint:
    operation: Operation
    # This is Flask's default hostname.
    hostname: str = "http://127.0.0.1:5000"


@dataclass
class ScaffoldModule:
    module_name: str


@dataclass
class ScaffoldConfig:
    output_directory: str
    application: Operation
    template_type: str | None = None
    modules: list[ScaffoldModule] | None = None
    module: dict[str, Any] = field(default_factory=dict)
    endpoints: list[ScaffoldEndpoint] | None = None
    mode: str = "create"


@final
class Scaffolder:
    def __init__(self, config: ScaffoldConfig, log: logging.Logger) -> None:
        self._config = config
        self._config_dict = asdict(config)
        self._log = log
        self._checked_directories: set[Path] = set()
        # BaseLoader is used for rendering strings only. It does not need additional functionality.
        self._base_env = Environment(
            loader=BaseLoader  # pyright: ignore[reportArgumentType]
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
            for example, in `{{application.module_name}}/modules/database/`, and the rendered template is `./__init__.py`, this default behavior
            is undesired. To resolve this, `template_directory_prefix` can be set in order to cause the rendered template to be stored under a
            different directory. For example, with the `template_directory_prefix` of `optional/{{application.module_name}}/modules/database/`, if the
            file `./__init__.py` is discovered at the template environment root,
            the file will instead be stored at `<output directory>/{{application.module_name}}/modules/database/__init__.py`.
        :param template_config: A dictionary of values that the template can reference.
        :param template: If provided, this template will be rendered instead of trying to discover the template with the name `template_name`
            in the template environment.
        :param overwrite_existing_files: If True, any existing files will be overwritten. If False, the template will not be rendered, and
            the file at the output location will not be overwritten.
        """
        if template_config is None:
            template_config = self._config_dict

        rendered_template_path = Path(
            # This causes paths with jinja2 directives to be rendered.
            # For example, if `self._config_dict['application'].module_name` is `foo`,
            # the path `base/{{application.module_name}}` is rendered as `base/foo`.
            self._render_template_string(template_name).replace(".j2", "")
        )
        # strip any leading / or c:/ etc. which should not occur here
        if rendered_template_path.is_absolute():
            rendered_template_path = path_separator.join(
                rendered_template_path.parts[1:]
            )

        template_output_path = Path(
            self._config.output_directory,
            template_directory_prefix,
            rendered_template_path,
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
        for template_name in env.list_templates(extensions=["j2"]):
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
            module_template_directory = f"scaffolding/templates/optional/{{{{application.module_name}}}}/modules/{module.module_name}"
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
                template_directory_prefix=f"{self._config.application.module_name}/modules/{module.module_name}",
                overwrite_existing_files=overwrite_existing_files,
            )

    def _scaffold_endpoints(
        self, env: Environment, overwrite_existing_files: bool = True
    ):
        """
        Render API endpoint templates.
        """
        # {{application.module_name}}/endpoints/{{operation.module_name}}.py.j2 is the file name - this is _not_ meant to be an interpolated string
        endpoint_template_filename = (
            "{{application.module_name}}/endpoints/{{operation.module_name}}.py.j2"
        )
        # technically, `self._config.endpoints` is always set in `__main__`
        # but we do this check to satisfy the type checker.
        if self._config.endpoints is None:
            self._log.debug("No endpoints to scaffold.")
            return

        # render optional API endpoint templates.
        # these templates are stored under `optional/` because:
        # 1. they are functionally optional. an application can be
        #    scaffolded without any endpoints, although `__main__` forces
        #    at least one endpoint (defaulting to the application name).
        # 2. more than one endpoint can be rendered, so a location
        #    for the templates that is not used to render an entire
        #    directory of templates (like the `base` templates) is needed.
        for endpoint in [asdict(_dataclass) for _dataclass in self._config.endpoints]:
            template = env.get_template(endpoint_template_filename)

            if template.name is None:
                self._log.error(
                    f"Could not find template `{endpoint_template_filename}`."
                )
                continue

            template_string_config = merge(self._config_dict.copy(), endpoint)

            # render the template output path, replacing the jinja2
            # directives with their associated values from `self._config_dict`.
            rendered_template_name = self._render_template_string(
                template.name, template_string_config
            )

            operation = endpoint["operation"]
            self._log.info(
                f'"{operation["url_path_name"]}" will be accessible at {endpoint["hostname"]}/{operation["url_path_name"]}'
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
    #      - the current directory is not a scaffolded application
    # it is safe for modify if:
    #      - the <application name> directory exists
    #      - the <application name> directory is a scaffolded application
    #      - the scaffolder is run from the scaffolded application's parent directory
    def _check_scaffolded_application_exists(self, test_path: Path):
        """
        Determine whether the application <config.application.module_name> is an importable
        BL_Python.web application that has been previously scaffolded with
        this tool.

        :param test_path: The directory to test for the existence of a scaffolded application.
        """
        application_import_path = Path(".", test_path)
        self._log.debug(
            f"Adding `{application_import_path}` to process module import path."
        )
        # modifying the import path to include a relative directory
        # is less than ideal and potentionally dangerous. we should
        # consider forking here or doing something else to prevent
        # the global modification.
        sys.path.insert(0, str(application_import_path))

        try:
            # if any of these steps fail, then the `test_path`
            # does not already contain a scaffolded application
            loader = SourceFileLoader(
                self._config.application.module_name,
                str(
                    Path(
                        test_path,
                        self._config.application.module_name,
                        "__init__.py",
                    )
                ),
            )
            mod = types.ModuleType(loader.name)
            sys.modules[self._config.application.module_name] = mod
            module = loader.load_module()
            _ = module.__version__
            _ = module._version.__bl_python_scaffold__
            # if no errors occur, then the `test_path`
            # contains a scaffolded application
            return True
        except Exception as e:
            self._log.debug(str(e), exc_info=True)
            return False
        finally:
            if self._config.application.module_name in sys.modules:
                del sys.modules[self._config.application.module_name]
            popped_import_path = sys.path.pop(0)
            self._log.debug(
                f"Popped `{popped_import_path}` from process module import path. Expected to pop `{application_import_path}`."
            )

    def scaffold(self):
        in_parent_directory = self._check_scaffolded_application_exists(
            Path(self._config.output_directory)
        )
        in_application_directory = self._check_scaffolded_application_exists(Path("."))

        # "create" can run from any directory that is not an existing
        # application's root directory.
        if self._config.mode == "create" and in_application_directory:
            self._log.critical(
                "Attmpted to scaffold a new application in the same directory as an existing application. This is not supported. Change your working directory to the application's parent directory, or run this from a directory that does not contain an existing application."
            )
            return

        # modify can only run from an existing application's
        # parent directory.
        if self._config.mode == "modify" and not in_parent_directory:
            self._log.critical(
                f"Attempted to modify an existing application from a directory that is not the existing application's parent directory. This is not supported. Change your working directory to the application's parent directory."
            )
            return

        if (
            # Only in create mode do we make absolutely certain that
            # the user is intentionally using a directory that
            # already exists, if it indeed does.
            self._config.mode == "create"
            and Path(self._config.output_directory).exists()
        ):
            self._log.debug(
                f"The directory `{self._config.output_directory}` already exists. Prompting the user whether to continue."
            )
            response = input(
                f"\nThe directory `{self._config.output_directory}` already exists. It is likely that files will be overwritten.\nDo you want to continue? [y/N] "
            )
            if not response.upper() == "Y":
                self._log.debug(f"User's input is `{response}`. Not continuing.")
                return
            self._log.debug(f"User's input is `{response}`. Continuing.")

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
