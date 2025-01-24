.. toctree::
   :maxdepth: 2
   :caption: Contents:

Creating the Application
------------------------

Now that we're set up to create a Ligare application, let's find out how to actually create one.

We will follow a structure that lets us write the application as a single Python "module," similar
to how `python-guide.org <https://docs.python-guide.org/writing/structure/>`_ demonstrates.

First create the module.

.. code-block:: shell-session

   user@: my-ligare-app $ mkdir app
   user@: my-ligare-app $ touch app/__init__.py app/__main__.py

Now we need to add some code to ``__main__.py``.

First, let's add some imports that our application depends on.

.. code-block:: python

   from Ligare.web.application import ApplicationBuilder
   from connexion import FlaskApp

We're going to write an application that displays a message at an API endpoint.

To do this, we need to do a few things:

1. Configure a ``FlaskApp`` instance
2. Create an application configuration file
2. Create the API endpoint

Configuring a FlaskApp Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get started, we will use ``ApplicationBuilder`` and tell Ligare we are creating a ``FlaskApp``
application.

.. code-block:: python

   application_builder = ApplicationBuilder(FlaskApp)

This gives us a builder that we can use to configure the application. Because our web application
needs a configuration file, we use the ``use_configuration`` method from the ``ApplicationBuilder``
instance to tell Ligare where to find our configuration file.

.. code-block:: python

   application_builder.use_configuration(
      lambda config_builder: \
         config_builder \
               .with_config_filename("app/config.toml")
   )

``use_configuration`` expects to receive a method that takes a single parameter.
That parameter type is itself an ``ApplicationConfigBuilder`` that is used to set
options specific to the configuration of a Ligare application.
`It's builders all the way down! <https://en.wikipedia.org/wiki/Turtles_all_the_way_down>`_

Lastly, we need to build the application and run it.

.. code-block:: python

   application = application_builder.build()

   if __name__ == "__main__":
      application.run()

This is the minimum required to get an instance of a Ligare web application.

Your application should resemble the Ligare example Web API application.

.. literalinclude:: ../../../../../examples/web-api/app/__main__.py
   :language: python
   :caption: :example:`web-api/app/__main__.py`

Creating the Application Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can now run this application with ``python -m app``, but we will get an error at this point.

.. code-block:: shell-session

   user@: my-ligare-app $ python -m app

   Ligare.programming.config.exceptions.ConfigInvalidError: The configuration file specified,
   `app/config.toml`, could not be found at `my-ligare-app/app/config.toml` and was not loaded.
   Is the file path correct?

Let's create the ``app/config.toml`` file.

.. literalinclude:: ../../../../../examples/web-api/app/config.toml
   :language: toml
   :caption: :example:`web-api/app/config.toml`

The options this file sets are the minimum required for a Ligare web application.

Creating the OpenAPI Specification File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Of special importance in the configuration file is the ``flask.openapi.spec_path`` option. Because we're creating
a ``FlaskApp`` application, we need to create an `OpenAPI specification <https://swagger.io/specification/>`_ file as well.

.. literalinclude:: ../../../../../examples/web-api/app/openapi.yaml
   :language: yaml
   :caption: :example:`web-api/app/openapi.yaml`

This file tells our application to create an endpoint at the url ``/``, and that
it can find a Python method to handle requests to ``/`` named ``get`` in the Python module ``app.root``.

Otherwise, don't worry too much about these contents for now!

Creating the Endpoint Request Handler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The last thing we need to do is to create the ``app.root`` module, and the ``get`` function that our
OpenAPI specification file states for the option ``operationId``.

.. literalinclude:: ../../../../../examples/web-api/app/root.py
   :language: python
   :caption: :example:`web-api/app/root.py`

Running the Application
^^^^^^^^^^^^^^^^^^^^^^^

Now we can run the application.

.. code-block:: console

   $ python -m app
   `ConnexionMiddleware.run` is optimized for development. For production, run using a dedicated ASGI server.
   INFO:     Started server process [25367]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://localhost:5000 (Press CTRL+C to quit)

Congrats! Your application is running. Now you can visit `<http://localhost:5000>`_ to see your application in action!
