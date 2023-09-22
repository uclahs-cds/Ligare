# `BL_Python.web` Scaffolder

This scaffolding tool exists to help people create a new `BL_Python.web` (or "BLApp") application by removing the tedium of setting up the initial requirements needed to start.

This document aims to explain how the scaffolding tool works.

# Templates

The scaffolding tool relies on Jinja2 templates to render file contents, and file and directory paths. The templates can be found under the `templates/` directory. Any files that can be rendered end with the extension `.j2`.

While Jinja2 is typically used to render HTML and related web files, this tool instead uses them to render Python, TOML, YAML, Markdown, etc. files as well as directory names.

## Template Rendering

Templates are broken up into several directories that each play a distinct role in the complete scaffolding of an application. Review [Template Directories](#template-directories) for more information.

The following order is used when rendering:

1. Modules
2. Base
3. Template Type
4. Endpoints

Each subsequent set of templates can overwrite files rendered from the previous sets. This means, for example, that a rendered template for Template Type, e.g. `openapi/{{application_name}}/endpoints/application.py.j2`, can overwrite the like-named rendered template `base/{{application_name}}/endpoints/application.py.j2` because the Template Type templates under `openapi/` are rendered after the Base templates under `base/`. This behavior is not inherent to Jinja2 and is a conscious decision regarding the behavior of the scaffolding tool.

Modules are able to modify the configuration and behavior of rendering, and so are executed first to allow this.

Note that directory names under each of the `templates/` directories can also contain Jinja2 directives as long as those directives also form a valid file name. For example, there are a couple of directories named `{{application_name}}/`. This is replaced with the name of the application and creates a directory with the name of the application under the output directory. For example, if `application_name` is "foo" then the directory will be named `foo/`.

### Template Configuration

Each template has access to the following configuration variables.

| Name | Type | What it is | Example |
| --- | --- | --- | --- |
| **output_directory** | `str` | The root directory that rendered templates will be stored under | `foo` |
| **application_name** | `str` | The name of the `BL_Python.web` application being scaffolded | `foo` |
| **template_type** | `str` | The type of template being scaffolded - either "basic" or "openapi" | `basic` |
| **modules** | `list[dict[str, Any]]` | A list of the dictionary form of the `ScaffoldModule` type. Contains information on modules to be scaffolded. | `[{'module_name': 'database'}]` |
| **module** | `dict[str, Any]` | A dynamically configured set of values set from each module's `on_create` hook. | `{'database': {'connection_string': 'sqlite:///:memory:'}}` |
| **endpoints** | `list[dict[str, Any]]` | A list of the dictionary form of the `ScaffoldEndpoint` type. Contains information on endpoints to be scaffolded. | `[{'endpoint_name': 'foo', 'hostname': 'http://127.0.0.1:5000'}]` |
| **endpoint** | `dict[str, Any]` | A dictionary form of the `ScaffoldEndpoint` type. For each endpoint to be rendered, this is set to the values for that endpoint and is only available within the templates being rendered for a given endpoint. | `{'endpoint_name': 'foo', 'hostname': 'http://127.0.0.1:5000'}` |
| **mode** | `str` | The scaffolding mode. Can either be `create` or `modify`. | `create` |

### Rendering Modes

The scaffolder has two modes: "create" and "modify." Create will create a completely new application, running through each step in the process. Modify only supports adding new API endpoints, and so only executes the rendering of templates under Endpoints.

## Template Directories

### Base

Templates under `base/` contain the essential files for a `BL_Python.web` application. This is the raw structure of such an application, and sets up the basics like:

1. Python application dependencies
2. README and other documentation / non-code files
3. The bare minimum to run a `BL_Python.web` application

All rendered files under `base/` can be replaced by rendered templates under `basic/` and `openapi/`.

While the template `base/{{application_name}}/endpoints/application.py.j2` can also be replaced, it generally should not be. This template provides default endpoints used by infrastructure tooling to manage web applications.

Templates under `base/` are rendered in a "glob" fashion, meaning all discovered templates are rendered and their structure is reflected in the output directory.

### Basic

Templates under `basic/` are used when rendering a "basic" `BL_Python.web` application. This is the default behavior of the scaffolder, and can also be set with the `-t basic` switch.

A "basic" template uses auto-discovery of Flask Blueprints to create API endpoints. This can be seen in the `optional/{{application_name}}/endpoints/{{endpoint_name}}.py.j2` template, which makes a distinction between template types.

Templates are `basic/` are also globbed.

### OpenAPI

Templates under `openapi/` are used when rendering an "openapi" `BL_Python.web` application. This can be done with the `-t openapi` switch.

An "openapi" template uses an `openapi.yaml` file to define endpoints and their request and response details.

OpenAPI applications do not use Flask Blueprints and so rely on a different structure of API template. As such, `base/{{application_name}}/endpoints/application.py.j2` is replaced to reflect this. You can also note the distinction in the `optional/{{application_name}}/endpoints/{{endpoint_name}}.py.j2` template.

Templates are `openapi/` are also globbed.

### Optional

Templates under `optional/` are templates that are rendered in unique ways as compared to the Base, Basic, and OpenAPI templates. Unlike the others, these templates are not globbed, and they might not be used for every application that is scaffolded.

#### Endpoints

Templates under `optional/endpoints/` are rendered once for every API endpoint that should be scaffolded. This is done with the `-e <endpoint>` switch, which can be specified multiple times.

These templates are aware of the scaffold template type and must make distinctions between the Basic and OpenAPI template types.

#### Modules

Templates under `optional/modules/` are rendered for each module specified with the `-m <module>` switch.

Modules are unique in that a callback can be specified that is executed when an application is being created. There is no callback available for when an application is modified. The available callbacks are:

##### `on_create(config: dict[str, Any], log: Logger) -> None`

This method can modify the configuration or do anything else necessary for the module and the other templates to render correctly.