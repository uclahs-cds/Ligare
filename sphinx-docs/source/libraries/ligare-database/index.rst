
.. _ligare-database:

Ligare.database
===============

``Ligare.database`` is a library for working with SQLite and PostgreSQL databases.
It integrates with `SQLAlchemy <https://www.sqlalchemy.org/>`_ as an `ORM <https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping>`_ library,
and extends `Alembic <https://alembic.sqlalchemy.org/en/latest/>`_ to help `manage your database <https://en.wikipedia.org/wiki/Schema_migration>`_ as it changes over time.

Why Use Ligare.database?
------------------------

``Ligare.database`` offers:

* SQLite *and* PostgreSQL without having to worry about database-specific behaviors

  * SQLite is often used for tests, while PostgreSQL is used for live applications
  * As an application grows, moving from SQLite to PostgreSQL is made simpler through ``Ligare.database``
  * Schemas with SQLite are made possible with ``Ligare.database``
* Integration with other parts of Ligare, for example, the configuration system, or ``Ligare.web`` web applications
* The same flexibility as SQLAlchemy with the functionality of Ligare
* Managed connections so you can set aside the complexity of database connectivity in an application

