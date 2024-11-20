.. toctree::
   :maxdepth: 2
   :caption: Contents:

Creating the Application
------------------------

Now that we're set up to create a Ligare application, let's find out how to actually create one.

We will follow a structure that lets us write the application as a single Python "module," similar to how `python-guide.org <https://docs.python-guide.org/writing/structure/>`_ demonstrates.

First create the module.

.. code-block:: shell-session

   user@: my-ligare-app $ mkdir app
   user@: my-ligare-app $ touch app/__init__.py

Now we need to add some code to ``__init__.py``.

Let's also explore a bit about how ``Ligare.web`` works.

First, ``Ligare.web`` uses a `builder <https://en.wikipedia.org/wiki/Builder_pattern>`_ to set up an instance of your application during runtime.
This allows us to `build` our application using specific functions to configure desired beavhiors and features.

.. seealso::

   A `builder <https://en.wikipedia.org/wiki/Builder_pattern>`_ is a pattern that helps programmers configure an instance of some other `type`.
   For this guide, it helps us configure an instance of ``FlaskApp``, which is the
   class name for the type of application we're creating.


The class we need for this is :obj:`ApplicationBuilder[T] <Ligare.web.application.ApplicationBuilder>`. We also need the application type. For this example, we're using `FlaskApp <https://github.com/spec-first/connexion/blob/3450a602fdd43b1d3a06581fd0106397b32e965b/connexion/apps/flask.py#L166>`_.

.. seealso::

   A "generic" class is a way to specify `generic` functionality for a range of more specific types.
   Here, we use the generic class :obj:`ApplicationBuilder[T] <Ligare.web.application.ApplicationBuilder>` to configure `generic` aspects of
   ``FlaskApp``.
   Here, the "generic type" is named ``T`` and is how we reference the more specific type that
   it represents.

   .. note:: 

      :obj:`ApplicationBuilder[T] <Ligare.web.application.ApplicationBuilder>` supports one other type of class called ``Flask``.
      Review `this guide <it doesn't exist yet>`_ to see how to create a ``Flask`` application.

Modify ``app/__init__.py`` with the following.

.. literalinclude:: ../../../../../examples/web-api/app/__init__.py
   :language: python

:download:`Download this example <../../../../../examples/web-api/app/__init__.py>`

Now we have something we can run. Go ahead and run this code.

.. code-block:: shell-session

   user@: my-ligare-app $ python app/__init__.py

Unfortunately, it seems we have another step to take because the application tells us it cannot find its configuration file.
That makes sense, because we haven't created it yet.

.. code-block:: console

   ConfigInvalidError: The configuration file specified, `app/config.toml`,
   could not be found at `/my-ligare-app/app/config.toml` and was not loaded.
   Is the file path correct?

Let's create that file.

.. code-block:: shell-session

   user@: my-ligare-app $ cat > app/config.toml <<EOF
   [logging]
   format = 'plaintext'

   [flask]
   app_name = 'app'
   EOF

.. note::

   Due to a `bug <https://github.com/uclahs-cds/Ligare/issues/158>`_ with JSON logging, plaintext logging must be configured.
   This format also makes it easier to read the output of your application in the console when you are building and testing it.

Run the application again.

.. code-block:: shell-session

   user@: my-ligare-app $ python app/__init__.py

Now you will see this.

.. code-block:: console

   * Serving Flask app 'app'
   * Debug mode: off
   WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
   * Running on http://localhost:5000
   Press CTRL+C to quit

Congrats! Your application is running. Now you can visit http://localhost:5000 to see your application in action!

But it doesn't do anything except tell you that nothing can be found.

.. code-block:: json

   {
     "error_msg": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
     "status": "Not Found",
     "status_code": 404
   }

This is because, while we do have a functional web application, we still haven't added any
API `endpoints` to it.
