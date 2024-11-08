Basic Applications
==================

At its core, a Basic scaffolded application is a `Flask <https://flask.palletsprojects.com/en/stable/>`_ application that uses `Blueprints <https://flask.palletsprojects.com/en/stable/blueprints>`_.
For a Basic application, Ligare provides a web framework that defines a structure for Flask applications, and provides functionality that Flask does not support on its own.

.. _basicendpointdifferences:

Endpoint Differences
--------------------

Because Basic applications use Blueprints, endpoint files contain both a Blueprint specification, and individual `route <https://flask.palletsprojects.com/en/stable/api/#flask.Flask.route>`_ definitions on each endpoint function.

Basic applications must contain only one Blueprint per endpoint file.

The ``application.py`` file contains an endpoint for the root URL of the application, which is ``/``. This endpoint displays a page with all registered endpoints for the running application
when the application is running in a "development" environment.
