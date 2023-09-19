# `BL_Python.web`

Libraries for building web applications in Boutros Lab.

# Quick Start

`BL_Python.web` includes a scaffolding tool to help you get started quickly.

"Scaffolding" is a common practice using tools and automation to create and modify applications without requiring any initial programming.

## Install Scaffolding

First install the `BL_Python.web` scaffolding tool. You can do this in your system Python install, or in a separate virtual environment.

Run these commands:

1. `pip install bl-python-programming@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/programming`
2. `pip install bl-python-web@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/web`

**Note** Once `BL_Python.web` is available in a package registry, the commands needed will change to `pip install bl-python-web` only.

## Scaffold a New Application

The command used is `bl-python-scaffold create`. Please run `bl-python-scaffold create -h` to review the possible options. The current options are explained here as well.

**Note** The command `bl-python-scaffold` has two modes: `create` and `modify`. The former is used to create a new application, while the latter is used to modify an existing one.

<details>
    <summary>Scaffold help</summary>

| Option | Explanation | Required? |
| --- | --- | --- |
| `-h` | Show the tool help text. | No |
| `-n <name>` | This is the name of your application. It is the name Flask will use to start up, and also acts as a default value for other options when they are not specified when running this tool. | Yes |
| `-e <endpoint>` | An optional endpoint to create. By default, an endpoint sharing the name of your application is created. If `-e` is specified even once, the default is _not_ created. This option can be specified more than once to create multiple endpoints. | No |
| `-t <type>` | The type of template to scaffold. This defaults to `basic`.<br /><br />`basic`: `BL_Python.web` searches your application for Flask "blueprint" files and uses them to create API endpoints. This is the easiest way to get started, but lacks some advantages of using `openapi`.<br /><br />`openapi`: `BL_Python.web` uses an OpenAPI spec file to describe API endpoints and their code location. This option is more complicated, however, it gives you the ability to validate your API endpoints during development, and allows for automatic request and response validation. It also gives you the ability to use Swagger as a test UI, which can be installed with `pip install connexion[swagger-ui]`. The OpenAPI spec file can also be fed into 3rd-party tools that further help with development. | No |
| `-m <module>` | Optional modules to include in your application. This option can be specified more than once to include multiple modules; however, currently the only available module is `database`.<br /><br />`database`: Include `BL_Python.database` and set up minimum requirements to utilize an SQLite database in your application. | No |
| `-o <output directory>` | Store the new application in a directory other than one that matches the application name. | No |

</details>
<br />

To create an application with a single API endpoint, run `bl-python-scaffold -n <name>` where `<name>` is replaced with the desired name of your application. By default, the scaffolder will output into a directory matching the name of your application. **Existing files will be overwritten.**

## Run Your Application

The scaffolder will have created several files and directories, including a README.md, under the output directory. Follow the instructions in your newly scaffolded application's README.md to run and configure your application.