Working With Scaffolded Applications
====================================

.. toctree::
	:maxdepth: 2
	:caption: Contents:
	:glob:

	*

Before continuing with this document, review :doc:`../create-application-with-scaffolder`.

This document covers the structure of scaffolded applications, how to run them, how to modify them,
and how to take advantage of the available modules.

Basic and OpenAPI Applications
------------------------------

Basic and OpenAPI applications share the same structure, with minor exception.
Most differences regard how to extend and modify the applications, and how they execute.
With that in mind, this section explores the shared aspects; the differences are in later sections.

Following the kitchen example in :doc:`../create-application-with-scaffolder`, this is the structure
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
