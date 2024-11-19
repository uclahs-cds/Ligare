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
This allows us to specify things like config files, application modules like ``Ligare.database``, and more. The class we need for this
is :obj:`ApplicationBuilder[T] <Ligare.web.application.ApplicationBuilder>`. We also need the application type. For this example, we're using `FlaskApp <https://connexion.readthedocs.io/en/2.9.0/autoapi/connexion/apps/flask_app/index.html#connexion.apps.flask_app.FlaskApp>`_.

Modify ``app/__init__.py`` with the following.

.. code-block:: python

   from Ligare.web.application import ApplicationBuilder
   from connexion import FlaskApp

   application_builder = ApplicationBuilder[FlaskApp]()

Now we have something we can run - but it doesn't do a whole lot. Go ahead and run this code.

.. code-block:: shell-session

   user@: my-ligare-app $ python app/__init__.py

As you can see, nothing really happens. This is because a builder needs to `build` what it has configured, and then something needs to be done with the built object.

Add this to the end of ``app/__init__.py``.

.. code-block:: python

   result = application_builder.build()

Now if we run the application, we get this error.

   InvalidBuilderStateError: Cannot build the application config without either `use_ssm` or `use_filename` having been configured.

We're getting there, but this error tells us that we still need to modify the builder to satisfy a requirement.
In this case, we need to add the method ``use_configuration``, and we need to add a config file.

Change ``app/__init__.py`` to look like this.

.. code-block:: python

   application_builder = ApplicationBuilder[FlaskApp]() \
      .use_configuration(
         lambda config_builder: \
            config_builder.with_config_filename("app/config.toml")
      )

   result = application_builder.build()

And create the config file.

.. code-block:: shell-session

   user@: my-ligare-app $ touch app/config.toml

Now if we run the application, we still get an error, but we're told that the config file is invalid.

   Exception: You must set [flask] in the application configuration

This is because we didn't actually put anything in the config file. So let's do that.

Change ``app/config.toml`` to the following.

.. code-block:: toml

   [flask]
   app_name = 'app'

Now if we run the application, we get a single line of output and the application exits.
Add one more line to ``app/__init__.py``. This tells the application to start accepting
API requests so that it doesn't just immediately exit.

.. code-block:: python

   result.app_injector.app.run()

Now you can visit http://localhost:5000 to see your application in action!

But it doesn't do anything except tell you that nothing can be found.

.. code-block:: json

   {
     "error_msg": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
     "status": "Not Found",
     "status_code": 404
   }

This is because, while we do have a functional web application, we still haven't added any
API `endpoints` to it.
