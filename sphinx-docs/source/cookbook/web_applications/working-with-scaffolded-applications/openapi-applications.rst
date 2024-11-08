OpenAPI Applications
====================

OpenAPI applications are `Connexion <https://connexion.readthedocs.io/en/stable/>`_ applications. Connexion extends Flask to enable the use of OpenAPI `specification <https://swagger.io/specification/>`_ files.
It also adds support for `Swagger UI <https://swagger.io/tools/swagger-ui/>`_ and a few other goodies.

.. _openapiendpointdifferences:

Endpoint Differences
--------------------
.. the section label alias replaces the section label,
.. so the warning that comes from autosectionlabel can
.. be ignored

OpenAPI applications do not use Blueprints. Instead, OpenAPI applications rely on an OpenAPI specification file, found at ``kitchen_openapi/openapi.yaml``.
Each API base URL is listed under ``paths``. Then, rather than using the route decorator, URLs are mapped to functions with the `OperationId <https://connexion.readthedocs.io/en/stable/routing.html#explicit-routing>`_
parameter for each HTTP operation.

The ``application.py`` file does not contain an endpoint to display all endpoints. Rather, Swagger UI is made available at the URL ``/ui``.
