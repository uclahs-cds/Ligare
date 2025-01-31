Database
========

.. toctree::
	:maxdepth: 2
	:caption: Contents:


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


.. _adding-tables:

Adding Tables
=============

.. code-block:: python

   class Bill(Base):
      __tablename__ = "bill"
      id = Column(Integer, primary_key=True)
      name = Column(String(50))

      def __repr__(self):
         return f"<Order {self.name}>"
