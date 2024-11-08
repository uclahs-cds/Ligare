Working With Scaffolded Applications
====================================

Before continuing with this document, review :doc:`create-application-with-scaffolder`.

This document covers the structure of scaffolded applications, how to run them, how to modify them,
and how to take advantage of the available modules.

Basic and OpenAPI Applications
------------------------------

Basic and OpenAPI applications share the same structure, with minor exception.
Most differences regard how to extend and modify the applications, and how they execute.
With that in mind, this section explores the shared aspects; the differences are in later sections.

Following the kitchen example in :doc:`create-application-with-scaffolder`, this is the structure
of an OpenAPI application that uses all modules.

.. code-block:: console

   $ ligare-scaffold create -t openapi \
      -n kitchen-openapi \
      -e order -e inventory -e chef \
      -m database \
      -m vscode \
      -m test

::

   .
   ├── alembic.ini
   ├── docs
   │   └── CONFIGURATION.md
   ├── kitchen_openapi
   │   ├── _app_type.py
   │   ├── config.toml
   │   ├── endpoints
   │   │   ├── application.py
   │   │   ├── chef.py
   │   │   ├── __init__.py
   │   │   ├── inventory.py
   │   │   └── order.py
   │   ├── __init__.py
   │   ├── __main__.py
   │   ├── modules
   │   │   ├── database
   │   │   │   ├── __init__.py
   │   │   │   └── migrations
   │   │   │       ├── env.py
   │   │   │       ├── env_setup.py
   │   │   │       ├── script.py.mako
   │   │   │       └── versions
   │   │   │           └── _
   │   │   ├── test
   │   │   │   ├── conftest.py
   │   │   │   ├── test_chef.py
   │   │   │   ├── test_inventory.py
   │   │   │   └── test_order.py
   │   │   └── vscode
   │   ├── openapi.yaml
   │   └── _version.py
   ├── LICENSE.md
   ├── Makefile
   ├── pyproject.toml
   └── README.md

There is only one additional file that the OpenAPI application contains that the Basic type does not,
which is ``kitchen_openapi/openapi.yaml``. :ref:`OpenAPI Applications` explains this further.

Endpoints
^^^^^^^^^

The endpoints for your API are found in ``kitchen_openapi/endpoints/``.

application.py
""""""""""""""

All applications contain an endpoint at the URL ``/healthcheck`` in the file ``application.py``, in the function ``healthcheck``.
This endpoint is for infrastructure purposes and does not typically need modification.
One use of this endpoint is for Docker's `HEALTHCHECK <https://docs.docker.com/reference/dockerfile/#healthcheck>`_ command.
For example, the Docker image can have Docker attempt to access the endpoint to determine when the container has started.

<endpoint name>.py
""""""""""""""""""

Every endpoint specified with ``-e`` during creation results in a separate file in the ``endpoints/`` directory.
As seen above, our Kitchen application contains ``order.py``, ``inventory.py``, and ``chef.py``.
These each correspond to the URLs, respectively, ``/order``, ``/invetory``, and ``/chef``.

Depending on the modules selected during creation, these files can contain a variety of functionality.
When the Database module is *not* selected, each file contains a single GET endpoint that returns a string.
When the Database module *is* selected, each file contains a GET and POST endpoint that, respectively, query or modify database records.

The contents of these files may be changed. Any number of endpoints may be added or removed, and their functionality
may fit whatever use case the application needs. Both Basic and OpenAPI application types have conventions that must be
complied with in order for these endpoints to be accessible. As well, any new endpoint URLs can be created in new <endpoint name>.py
files.

Modules
^^^^^^^

The selected modules usually contain code in the ``kitchen_openapi/modules/`` directory.

Database
""""""""

The Database module is stored at ``kitchen_openapi/modules/database/``, and consists of two major
sets of functionality: table definitions, and migrations. Working with the database is done through
the `SQLAlchemy <https://www.sqlalchemy.org/>`_ library, while database migrations are handled by the
`Alembic <https://alembic.sqlalchemy.org/en/latest/>`_ library and the ``ligare-alembic`` command.

In ``__init__.py``, the module creates basic table definition classes for each endpoint specified during creation.
The class names match end endpoint names, and each contains an ``id`` and ``name`` field. These classes (and table names)
can be renamed, extended, or moved around (as long as references are updated).

For database migrations, see ``ligare-alembic --help``. This command is largely a wrapper for Alembic,
so most of what applies to Alembic also applies here. The major difference lies in ``ligare-alembic``'s
integration with the rest of Ligare.

Test
""""

The Test module is stored at ``kitchen_openapi/modules/test``. The module creates separate files, named ``test_<endpoint name>.py``
for each endpoint specified during creation. The module also creates tests for your application. Because Ligare uses ``pytest``, the same
rules and behavior for ``pytest`` apply to tests created for your application.

If the Database module is also specified during creation, the Test module will create additional tests for the storage and retrieval
of data through the endpoint URLs created. To support this, an in-memory SQLite database is configured through the ``use_inmemory_database``
fixture in ``conftest.py``.

VSCode
""""""

The VSCode module is stored at ``kitchen_openapi/.vscode/``. This module creates a ``launch.json`` file that allows you to debug your application
through VSCode. Two debugger configurations are created: one to debug the currently focused file, and one to start and debug your application.

Basic Applications
------------------

At its core, a Basic scaffolded application is a `Flask <https://flask.palletsprojects.com/en/stable/>`_ application that uses `Blueprints <https://flask.palletsprojects.com/en/stable/blueprints>`_.
For a Basic application, Ligare provides a web framework that defines a structure for Flask applications, and provides functionality that Flask does not support on its own.

.. _basicendpointdifferences:

Endpoint Differences
^^^^^^^^^^^^^^^^^^^^

Because Basic applications use Blueprints, endpoint files contain both a Blueprint specification, and individual `route <https://flask.palletsprojects.com/en/stable/api/#flask.Flask.route>`_ definitions on each endpoint function.

Basic applications must contain only one Blueprint per endpoint file.

The ``application.py`` file contains an endpoint for the root URL of the application, which is ``/``. This endpoint displays a page with all registered endpoints for the running application
when the application is running in a "development" environment.

OpenAPI Applications
--------------------

OpenAPI applications are `Connexion <https://connexion.readthedocs.io/en/stable/>`_ applications. Connexion extends Flask to enable the use of OpenAPI `specification <https://swagger.io/specification/>`_ files.
It also adds support for `Swagger UI <https://swagger.io/tools/swagger-ui/>`_ and a few other goodies.

.. _openapiendpointdifferences:

Endpoint Differences
^^^^^^^^^^^^^^^^^^^^

OpenAPI applications do not use Blueprints. Instead, OpenAPI applications rely on an OpenAPI specification file, found at ``kitchen_openapi/openapi.yaml``.
Each API base URL is listed under ``paths``. Then, rather than using the route decorator, URLs are mapped to functions with the `OperationId <https://connexion.readthedocs.io/en/stable/routing.html#explicit-routing>`_
parameter for each HTTP operation.

The ``application.py`` file does not contain an endpoint to display all endpoints. Rather, Swagger UI is made available at the URL ``/ui``.
