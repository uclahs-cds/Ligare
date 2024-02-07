# `BL_Python.web`

Libraries for building web applications in Boutros Lab.

# Quick Start

`BL_Python.web` includes a scaffolding tool to help you get started quickly.

"Scaffolding" is a common practice using tools and automation to create and modify applications without requiring any initial programming.

## Install Scaffolding

First install the `BL_Python.web` scaffolding tool. You can do this in your system Python install, or in a separate virtual environment. Read more about virtual environments at [docs.python.org](https://docs.python.org/3/library/venv.html) or [realpython.com](https://realpython.com/python-virtual-environments-a-primer/).

Install necessary dependencies:

- `pip install bl-python.web`

## Scaffold a New Application

The command used is `bl-python-scaffold create`. Please run `bl-python-scaffold create -h` to review the possible options. The current options are explained here as well.

**🚩** The command `bl-python-scaffold` has two modes: `create` and `modify`. The former is used to create a new application, while the latter is used to modify an existing one.

<details>
    <summary>Scaffold "create" help</summary>

These options are for the `bl-python-scaffold create` command.

| Option | Explanation | Required? |
| --- | --- | --- |
| `-h` | Show the tool help text. | No |
| `-n <name>` | This is the name of your application. It is the name Flask will use to start up, and also acts as a default value for other options when they are not specified when running this tool. | Yes |
| `-e <endpoint>` | An optional endpoint to create. By default, an endpoint sharing the name of your application is created. If `-e` is specified even once, the default is _not_ created. This option can be specified more than once to create multiple endpoints. | No |
| `-t <type>` | The type of template to scaffold. This defaults to `basic`.<br /><br />`basic`: `BL_Python.web` searches your application for Flask "blueprint" files and uses them to create API endpoints. This is the easiest way to get started, but lacks some advantages of using `openapi`.<br /><br />`openapi`: `BL_Python.web` uses an OpenAPI spec file to describe API endpoints and their code location. This option is more complicated, however, it gives you the ability to validate your API endpoints during development, and allows for automatic request and response validation. It also gives you the ability to use Swagger as a test UI, which can be installed with `pip install connexion[swagger-ui]`. The OpenAPI spec file can also be fed into 3rd-party tools that further help with development. | No |
| `-m <module>` | Optional modules to include in your application. This option can be specified more than once to include multiple modules; however, currently the only available module is `database`.<br /><br />`database`: Include `BL_Python.database` and set up minimum requirements to utilize an SQLite database in your application. | No |
| `-o <output directory>` | Store the new application in a directory other than one that matches the application name. | No |

</details>
<details>
    <summary>Scaffold "modify" help</summary>

These options are for the `bl-python-scaffold modify` command.

| Option | Explanation | Required? |
| --- | --- | --- |
| `-h` | Show the tool help text. | No |
| `-n <name>` | This is the name of your application. It is the name Flask will use to start up, and also acts as a default value for other options when they are not specified when running this tool. | Yes |
| `-e <endpoint>` | An endpoint to create. By default, an endpoint sharing the name of your application is created. If `-e` is specified even once, the default is _not_ created. This option can be specified more than once to create multiple endpoints. | No |
| `-o <output directory>` | Modify the application in a directory other than one that matches the application name. | No |

</details>
<br />
<br />

To create an application with a single API endpoint, run `bl-python-scaffold create -n <name>` where `<name>` is replaced with the desired name of your application. By default, the scaffolder will output into a directory matching the name of your application. **❗ Existing files will be overwritten.**

**🚩** Scaffolding modules can only be done during creation of the application. If you need database functionality, for example, be sure to include `-m database`!

## Run Your Application

The scaffolder will have created several files and directories, including a README.md, under the output directory. Follow the instructions in your newly scaffolded application's README.md to run and configure your application.

# About the Library

`BL_Python.web` is intended to handle a lot of the boilerplate needed to create and run Flask applications. A primary component of that boilerplate is tying disparate pieces of functionality and other libraries together in a seamless way. For example, [SQLAlchemy](https://www.sqlalchemy.org/) is an ORM supported through `BL_Python.database` that this library integrates with to make database functionality simpler to make use of.

## Flask

`BL_Python.web` is based on [Flask 3.0.x](https://flask.palletsprojects.com/en/3.0.x/) and [Connexion 3.0.x](https://connexion.readthedocs.io/en/3.0.5/).

## Development

Development dependencies can be installed with `[dev-dependencies]`. If developing from the core repository, use the command `pip install -e src/web[dev-dependencies]`.
