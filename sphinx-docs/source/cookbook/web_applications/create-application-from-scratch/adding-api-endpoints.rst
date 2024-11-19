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

First, let's modify the application config file ``app/config.toml``. Add the ``flask.openapi`` section so your file looks like this.

.. code-block:: toml

   [flask]
   app_name = 'app'

   [flask.openapi]
   spec_path = 'openapi.yaml'


.. code-block:: python

   from Ligare.web.config import Config

   application_builder = (
      ApplicationBuilder[FlaskApp]()
      .use_configuration(
            lambda config_builder: config_builder
            .with_config_filename("app/config.toml")
            .with_root_config_type(Config)
      )
   )
   result = application_builder.build()
