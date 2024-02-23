# `BL_Python.web`

Libraries for building web applications in Boutros Lab.

# Quick Start

`BL_Python.web` includes a scaffolding tool to help you get started quickly.

"Scaffolding" is a common practice using tools and automation to create and modify applications without requiring any initial programming.

Review [Creating a New BL_Python.web Application](https://github.com/uclahs-cds/BL_Python/wiki/Creating-a-New-BL_Python.web-Application) for detailed information.

# About the Library

`BL_Python.web` is intended to handle a lot of the boilerplate needed to create and run Flask applications. A primary component of that boilerplate is tying disparate pieces of functionality and other libraries together in a seamless way. For example, [SQLAlchemy](https://www.sqlalchemy.org/) is an ORM supported through `BL_Python.database` that this library integrates with to make database functionality simpler to make use of.

## Flask

`BL_Python.web` is based on [Flask 3.0.x](https://flask.palletsprojects.com/en/3.0.x/) and [Connexion 3.0.x](https://connexion.readthedocs.io/en/3.0.5/).

## Development

Development dependencies can be installed with `[dev-dependencies]`. If developing from the core repository, use the command `pip install -e src/web[dev-dependencies]`.
