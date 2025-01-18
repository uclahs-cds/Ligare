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

We need to have your application load the OpenAPI specification file, which is used to control the details of your API.

Let's modify the application config file ``app/config.toml`` to add the ``flask.openapi`` section.

.. code-block:: shell-session

   user@: my-ligare-app $ cat >> app/config.toml << EOF
   [flask.openapi]
   spec_path = 'openapi.yaml'

   EOF

Your file will look like this.

.. literalinclude:: ../../../../../examples/web-api/app/config.toml
  :language: toml
  :caption: :example:`web-api/app/config.toml`

Adding Endpoints
^^^^^^^^^^^^^^^^

With these preliminary adjustments completed, we can add a new endpoint.

We're going to add an endpoint to handle requests made to the root URL, ``/``, of the application.
This means accessing http://localhost:5000 will show the "Hello, World!" message we're expecting.

The ``openapi.yaml`` File
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a new file at ``app/openapi.yaml`` and add this content.

.. literalinclude:: ../../../../../examples/web-api/app/openapi.yaml
   :language: yaml
   :caption: :example:`web-api/app/openapi.yaml`

This OpenAPI specification states that there is an HTTP GET endpoint at
``/`` that returns an HTTP 200 status, and a JSON string for its content.

Pay special attention to the ``operationId`` property. This tells Connexion
that it can find a function named ``get`` in the Python module named ``root``.

The Endpoint Handler
~~~~~~~~~~~~~~~~~~~~

Finally, let's create the Python module and function that will handle requests
for this endpoint.

Create the file ``app/root.py`` and add this to it.

.. literalinclude:: ../../../../../examples/web-api/app/root.py
   :language: python
   :caption: :example:`web-api/app/root.py`

The function named ``get`` is the same one specified for the ``operationId`` property.
This is all you need to do to return data through your API endpoint!

Now you can start the application with ``python app/__init__.py``. Once it's running,
open http://localhost:5000/ and you should see "Hello, World!"
