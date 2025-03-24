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
-----------------

Let's extend the Kitchen application with two new endpoints:

* One for billing an order
* One for the menu

Considering that a user is billed for their order, and we already have a base URL and endpoint file for ``/order``,
we will add a new endpoint URL to the file. Open the file ``kitchen_flask/endpoints/order.py`` and add the following.

.. code-block:: python

   @inject
   @order_blueprint.route("/bill")
   def get_order_bill(session: Session):
      order_id = int(request.args.get('order_id'))

This adds a new function that is executed when the URL ``/order/bill`` is accessed.
The function is given an instance of the `Session <https://docs.sqlalchemy.org/en/14/orm/session.html>`_ type from SQLAlchemy,
and it gets the values of a URL parameter called ``order_id`` from the full URL ``/order/bill?order_id=123``.
Right now the function doesn't do anything, so let's add something to it.

.. code-block:: python

   @inject
   @order_blueprint.route("/bill")
   def get_order(session: Session):
      order_id = int(request.args.get('order_id'))

      bill = session \
         .query(Order) \
         .join(Bill) \
         .filter(Order.id == order_id) \
         .one()

With this, the function queries the database for the order and its associated bill, but the function still doesn't
send anything back to the requester of the data. We can do that by returning a dictionary assembled from the data.
This works because Flask will turn a dictionary into `JSON <https://flask.palletsprojects.com/en/stable/patterns/javascript/#return-json-from-views>`_
that the requester can work with.

.. code-block:: python

   @inject
   @order_blueprint.route("/bill")
   def get_order(session: Session):
      order_id = int(request.args.get('order_id'))

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

You now have enough information to add your own endpoints! However, to make this example functional we also need to add
a new database table. Review :ref:`adding-tables` ...
