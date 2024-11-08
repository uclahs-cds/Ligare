Modules
========

The selected modules usually contain code in the ``kitchen_openapi/modules/`` directory.

Database
--------

The Database module is stored at ``kitchen_openapi/modules/database/``, and consists of two major
sets of functionality: table definitions, and migrations. Working with the database is done through
the `SQLAlchemy <https://www.sqlalchemy.org/>`_ library, while database migrations are handled by the
`Alembic <https://alembic.sqlalchemy.org/en/latest/>`_ library and the ``ligare-alembic`` command.

In ``__init__.py``, the module creates basic table definition classes for each endpoint specified during creation.
The class names match end endpoint names, and each contains an ``id`` and ``name`` field. These classes (and table names)
can be renamed, extended, or moved around (as long as references are updated).

For database migrations, see ``ligare-alembic --help``. This command is largely a wrapper for Alembic,
so most of what applies to Alembic also applies here. The major difference lies in ``ligare-alembic``'s
integration with the rest of Ligare. In addition to using migrations, the Database module configures the
application to create the database when the application first starts. This behavior can be found in
``kitchen_openapi/__init__.py`` where ``Base.metadata.create_all(...)`` is called, and can be removed
if this behavior is not desired.

Test
----

The Test module is stored at ``kitchen_openapi/modules/test``. The module creates separate files, named ``test_<endpoint name>.py``
for each endpoint specified during creation. The module also creates tests for your application. Because Ligare uses ``pytest``, the same
rules and behavior for ``pytest`` apply to tests created for your application.

If the Database module is also specified during creation, the Test module will create additional tests for the storage and retrieval
of data through the endpoint URLs created. To support this, an in-memory SQLite database is configured through the ``use_inmemory_database``
fixture in ``conftest.py``.

VSCode
-------

The VSCode module is stored at ``kitchen_openapi/.vscode/``. This module creates a ``launch.json`` file that allows you to debug your application
through VSCode. Two debugger configurations are created: one to debug the currently focused file, and one to start and debug your application.
