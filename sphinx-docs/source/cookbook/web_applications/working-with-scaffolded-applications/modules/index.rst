Modules
========

.. toctree::
	:maxdepth: 2
	:caption: Contents:

   database

The selected modules usually contain code in the ``kitchen_openapi/modules/`` directory.


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
