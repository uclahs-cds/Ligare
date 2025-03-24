
Ligare Libraries
================

Ligare is a collection of libraries and utilities for creating new applications,
or extending existing applications.

.. contents::
   :depth: 2
   :local:

.. toctree::
   :maxdepth: 2
   :hidden:
   :glob:

   */index
   structure


Why Use Ligare?
----------------

Here are some use cases for using Ligare in your application,
or for creating new applications.

For Web Applications
^^^^^^^^^^^^^^^^^^^^

* You want to create a new web application without worrying about its structure and dependencies
* You want to write automated tests for web applications
* You want to extend an existing Flask or Connexion application with Ligare middleware

For Command Line Applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* You need a sophiscated command line application and the utilities to support one, without writing the complexity yourself

For Databases
^^^^^^^^^^^^^

* You want to use either or both of SQLite and PostgreSQL in your application
* You want to write automated tests for database usage

For User Authentication and Authorization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* You need to authenticate users through SSO
* You need to control authenticated user access to parts of your application

For Advanced Runtime Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* You have configuration requirements that environment variables are insufficient to meet
* You need to use AWS SSM for secure application configuration

For Sophisicated Application Architecture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* You want to use dependency injection throughout an application
* You want to use design patterns that are challenging to implement in Python, like singletons

For Combining All of the Above
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* You need to use a database in a web application
* You need to control user access in a web application
* You need a command line application to get a connection string from AWS SSM in order to connect to a database
