.. toctree::
   :maxdepth: 2
   :caption: Contents:

Additional Features
-------------------

Swagger UI
^^^^^^^^^^

``Ligare.web`` ships with `Swagger UI <https://swagger.io/tools/swagger-ui/>`_, which makes manually testing your API simple.

By default, the URL ``/ui`` is reserved so you can access this tool at http://localhost:5000/ui when your application is running.

The Swagger UI URL takes precendence over any specified in your openapi.yaml file; that is, if you use ``/ui`` in your OpenAPI specification,
it will be ignored.
