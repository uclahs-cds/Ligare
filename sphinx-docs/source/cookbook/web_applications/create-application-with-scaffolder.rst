Create an Application With the Scaffolder
=========================================

``Ligare.web`` contains a scaffolder to quickly create web applications.

Prerequisites
-------------

* Install ``Ligare.web``:

.. code-block:: console

    $ pip install ligare.web

Creating Applications
--------------------------

The command ``ligare-scaffold`` is used to create web applications. It supports two types of web applications:

* "basic" which creates a simple Flask application
* "openapi" which creates a Connexion application that uses OpenAPI

All command line options can be found with the following:

.. code-block:: console

    $ ligare-scaffold -h
    $ ligare-scaffold create -h
    $ ligare-scaffold modify -h

The examples seen here will all create a new application from scratch, using the options specified at the command line.

For example purposes, we will see what it's like to create an application called **Kitchen**.
Kitchen takes **order**\ s, has an **inventory**, and delegates work to **chef**\ s.

Create a "basic" Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Choose to make a "basic" application when you only need API endpoints with no advanced features.

For **kitchen**, we may decide to make a "basic" application because it represents a kitchen
in a house. No **order**\ s are taken, **inventory** exists but is likely simple enough to
manage that a separate *endpoint* is not neccessary, and there is only one **chef**.

.. code-block:: console

    # Create an application named "kitchen" with a single endpoint at /kitchen
    $ ligare-scaffold create -t basic -n kitchen

Create an "openapi" Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Choose to make an "openapi" application when you want to:

* Use an OpenAPI specification for your API
* Gain access to SwaggerUI
* Take advantage of ASGI middleware

For **kitchen**, we may decide to make an "openapi" application because it represents a kitchen
for a restaurant. For this example, consider a small kitchen like a burger stand. It does
take **order**\ s, **inventory** only includes burger ingredients, and there is only one **chef**.

The API for this can use a single *endpoint* like the home kitchen example, but with the "openapi"
application, we can do things like create ASGI middleware that automatically bills a customer
when an **order** comes in.

.. code-block:: console

    # Create an application named "kitchen" with a single endpoint at /kitchen
    $ ligare-scaffold create -t openapi -n kitchen


Adding Endpoints to the Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most web applications have more than one "endpoint" in their API. This allows for clearer organization of where functionality is contained.

The scaffolder helps with adding the initial endpoints for your application through the use of the ``-e`` switch.

For our kitchen example, let's consider a busier restaurant with a full menu for **order**\ s, more complex
**inventory** requirements, and multiple **chef**\ s. It is usually easier to manage this complexity by segmenting
these components into different API *endpoints*.

.. code-block:: console

    # Create a "basic" application with endpoints at /order, /inventory, and /chef
    $ ligare-scaffold create -t basic -n kitchen -e order -e inventory -e chef

    # Create an "openapi" application with endpoints at /order, /inventory, and /chef
    $ ligare-scaffold create -t openapi -n kitchen -e order -e inventory -e chef

By default, the scaffolder creates an endpoint that matches the name of your application, as seen in the earlier examples.
Specifying endpoints with ``-e`` is optional. When ``-e`` is used, an endpoint sharing the name of the applicaiton is not
created and would need to be specified with ``-e``.

Using Modules
-------------

The scaffolder contains "modules" that add functionality to your application when it is created.
These modules are selected using with the ``-m`` switch.
More than one module can be specified by using ``-m`` multiple times, e.g., ``-m database -m test``.

Access a Database in your Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Database module sets up basic functionality to work with databases through SQLAlchemy, and can be set up like this.

.. code-block:: console

    $ ligare-scaffold create -n kitchen -m database

The Database module expects additional input so your application knows how to connect to your database.

.. code-block:: console

    Enter a database connection string.
    By default this is `sqlite:///:memory:?check_same_thread=False`.
    Retain this default by pressing enter, or type something else.
    >

The default value allows your application to use an in-memory database. This is fine for data that does not need to be retained,
but that data is lost every time your application restarts. You may want to use a filesystem database like this.

.. code-block:: console

    sqlite:///kitchen.db

When your application first runs, an SQLite database is created at the root of your application directory with the name ``kitchen.db``.

Debugging in VSCode
^^^^^^^^^^^^^^^^^^^

The scaffolder contains a module that makes it easy to debug your application when using VSCode.

.. code-block:: console

    ligare-scaffold create -n kitchen -m vscode

The creates ``.vscode/launch.json`` at the root of your application directory, which VSCode uses to start the Python debugger.

Creating Automated Tests
^^^^^^^^^^^^^^^^^^^^^^^^

The scaffolder contains a module that generates initial automated tests for your application.

.. code-block:: console

    ligare-scaffold create -n kitchen -m test

The Test module will create additional tests when the Database module is also specified.

.. code-block:: console

    ligare-scaffold create -n kitchen -m database -m test

.. note::

    Due to a `bug <https://github.com/uclahs-cds/Ligare/issues/149>`_, the creation of database tests only occurs if ``-m database`` is specified before ``-m test``.
