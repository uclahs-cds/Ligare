.. toctree::
   :maxdepth: 2
   :caption: Contents:

Adding API Endpoints
--------------------

Adding an API endpoint to a `FlaskApp` application requires two things:

* A Python function to respond to an API request
* A `specification` to tell the application what the endpoint is, and where to handle requests

The Python functions are regular functions that you're already familiar with.
The specification is an `OpenAPI specification <https://swagger.io/specification/>`_ written in a YAML file.

Modifying the Existing Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, let's modify the application config file ``app/config.toml``. Add the ``flask.openapi`` section so your file looks like this.

.. code-block:: toml

   [flask]
   app_name = 'app'

   [flask.openapi]
   spec_path = 'openapi.yaml'

This change allows us to use an OpenAPI specification file to control details of the API endpoint.

We also need to modify the ``[flask]`` section, and add a ``[logging]`` section.

Your file will look like this.

.. code-block:: toml

   [flask]
   app_name = 'app'
   host = 'localhost'
   port = '5000'

   [flask.openapi]
   spec_path = 'openapi.yaml'

   [logging]
   format = 'plaintext'

Finally, let's make a few modifications to ``app/__init__.py``.
This ensures the ``localhost`` and ``port`` options in ``config.toml`` are used.

.. code-block:: python

   from Ligare.web.config import FlaskConfig

   application_builder = ApplicationBuilder[FlaskApp]() \
      .use_configuration(
         lambda config_builder: \
            config_builder.with_config_filename("app/config.toml")
      )

   result = application_builder.build()
   app = result.app_injector.app

   injector = result.app_injector.flask_injector.injector
   config = injector.get(FlaskConfig)
   app.run(host=config.host, port=int(config.port))

Adding Endpoints
^^^^^^^^^^^^^^^^

With these preliminary adjustments completed, we can add a new endpoint.

We're going to add an endpoint to handle requests made to the root URL, ``/``, of the application.
This means accessing http://localhost:5000 will show the "Hello, World!" message we're expecting.

The ``openapi.yaml`` File
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a new file at ``app/openapi.yaml`` and add this content.

.. code-block:: yaml

   info:
     title: Test Application
     version: 3.0.3
   openapi: 3.0.3
   paths:
     /:
       get:
         description: Say "Hello, World!"
         operationId: root.get
         responses:
           "200":
             content:
               application/json:
                 schema:
                   type: string
             description: Said "Hello, World!" successfully


This OpenAPI specification states that there is an HTTP GET endpoint at
``/`` that returns an HTTP 200 status, and a JSON string for its content.

Pay special attention to the ``operationId`` property. This tells Connexion
that it can find a function named ``get`` in the Python module named ``root``.

The Endpoint Handler
~~~~~~~~~~~~~~~~~~~~

Finally, let's create the Python module and function that will handle requests
for this endpoint.

Create the file ``app/root.py`` and add this to it.

.. code-block:: python

   def get():
      return "Hello, World!"

The function named ``get`` is the same one specified for the ``operationId`` property.
This is all you need to do to return data through your API endpoint!

Now you can start the application with ``python app/__init__.py``. Once it's running,
open http://localhost:5000/ and you should see "Hello, World!"
