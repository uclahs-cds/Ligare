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

Adding Endpoints
================

Let's extend the Kitchen application with two new endpoints:

* One for billing an order
* One for the menu

Considering that a user is billed for their order, and we already have a base URL and endpoint file for ``/order``,
we will add a new endpoint URL to the file. Open the file ``kitchen_flask/endpoints/order.py`` and add the following.

.. code-block:: python

   @inject
   @order_blueprint.route("/bill")
   def get_order(session: Session):
       # bill = {"orderId": "123", "items": [{"name": "burger", "price": 5.0, "amount": 1}, {"name": "cake", "price": 6.0, "amount": 1}]}
       bill = session \
         .query(Order) \
         .join(Bill) \
         .one()

      return dict([(
         item["name"],
         {
            "price": item["price"],
            "amount": item["amount"]
         })
         for item in bill["items"]
      ])

.. also need to add an example of adding tables
