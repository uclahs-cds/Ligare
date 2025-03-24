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

Adding Endpoints
^^^^^^^^^^^^^^^^

In the previous guide, we added an endpoint to handle requests to the URL ``/``. Here we
will see how to add an endpoint URL named ``/greet/name`` that will show the text "Hello, name!"

The ``openapi.yaml`` File
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a new entry nested in ``paths`` in the ``app/openapi.yaml`` file.

.. code-block:: yaml

   paths:
      ...
      /greet/{name}:
         get:
            description: Say "Hello, name!"
            parameters:
               - in: path
               name: name
               schema:
                  type: string
               required: true
               description: The name to greet
            operationId: app.greet.get
            responses:
               "200":
               content:
                  application/json:
                     schema:
                     type: string
               description: Said "Hello, name!" successfully

There is a little bit more going on here. Because we want to greet someone other than "world,"
this specification states there is a parameter ``name`` that is a string in the path. Otherwise,
this matches the URL endpoint specification for ``/``.


The Endpoint Handler
~~~~~~~~~~~~~~~~~~~~

Just like ``app.root.get``, we need to create a Python module and method matching the ``operationId``.

Create the file ``app/greet.py`` with this content.

.. code-block:: python

   import re

   def get(name: str):
      name_safe = re.sub(r"[^a-zA-Z0-9]", "", name)
      return f"Hello, {name_safe}!"

.. important::

   **Never** trust input in your application! Here, we ensure that the name we display
   only contains alphanumeric characters. Otherwise, we could end up with an `XSS <https://owasp.org/www-community/attacks/xss/>`_
   vulnerability or worse!

Now we can start our application and visit `<http://localhost:5000/greet/example>`_ to see "Hello, example!"
