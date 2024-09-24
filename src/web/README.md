# `Ligare.web`

Libraries for building web applications.

# Quick Start

`Ligare.web` includes a scaffolding tool to help you get started quickly.

"Scaffolding" is a common practice using tools and automation to create and modify applications without requiring any initial programming.

Review [Creating a New Ligare.web Application](https://github.com/uclahs-cds/Ligare/wiki/Creating-a-New-Ligare.web-Application) for detailed information.

# About the Library

`Ligare.web` is intended to handle a lot of the boilerplate needed to create and run Flask applications. A primary component of that boilerplate is tying disparate pieces of functionality and other libraries together in a seamless way. For example, [SQLAlchemy](https://www.sqlalchemy.org/) is an ORM supported through `Ligare.database` that this library integrates with to make database functionality simpler to make use of.

## Flask

`Ligare.web` is based on [Flask 3.0.x](https://flask.palletsprojects.com/en/3.0.x/) and [Connexion 3.0.x](https://connexion.readthedocs.io/en/3.0.5/).

## Development

Development dependencies can be installed with `[dev-dependencies]`. If developing from the core repository, use the command `pip install -e src/web[dev-dependencies]`.
