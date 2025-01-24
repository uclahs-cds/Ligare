.. toctree::
   :maxdepth: 2
   :caption: Contents:

Creating the Application
------------------------

Now that we're set up to create a Ligare application, let's find out how to actually create one.

We will follow a structure that lets us write the application as a single Python "module," similar
to how `python-guide.org <https://docs.python-guide.org/writing/structure/>`_ demonstrates.

First create the module.

.. code-block:: shell-session

   user@: my-ligare-app $ mkdir app
   user@: my-ligare-app $ touch app/__init__.py app/__main__.py

Now we need to add some code to ``__main__.py``.

First, let's add some imports that our application depends on.

.. code-block:: python

   from injector import inject
   from Ligare.programming.application import ApplicationBase, ApplicationBuilder
   from typing_extensions import override

We're going to write an application that displays a message stored in a configuration file.

To do this, we need to do a few things:

1. Create an ``Application`` class
2. Create a ``Config`` class and file
3. Configure the application

Creating the Application Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All Ligare applications are extensions of ``ApplicationBase``. These classes must implement a
``run`` method, which can use the Ligare dependency injection system.

.. code-block:: python

   class Application(ApplicationBase):
      @override
      def run(self):
         print("Hello world!")
         input("\nPress anything to exit. ")

Here, we have created a class called ``Application`` that extends ``ApplicationBase``.

Although we could run our application by instantiating ``Application`` and calling ``run``,
we would lose out on what Ligare care do for us. To take advantage of that functionality,
we will use ``ApplicationBuilder``.

.. code-block:: python

   builder = ApplicationBuilder(Application)

This gives us a builder for our ``Application`` class with which we can configure the
application, and then start it.

This is the minimum required to set up our application. We can now "build" it,
and then start it.


.. code-block:: python

   application = builder.build()

   if __name__ == "__main__":
      application.run()

Our completed application looks like this.

.. code-block:: python

   from injector import inject
   from Ligare.programming.application import ApplicationBase, ApplicationBuilder
   from typing_extensions import override

   class Application(ApplicationBase):
       @inject
       @override
       def run(self):
           print("Hello, world!")
           input("\nPress anything to exit. ")

   builder = ApplicationBuilder(Application)

   application = builder.build()

   if __name__ == "__main__":
       application.run()

When we run the application, we see the expected output.

.. code-block:: shell-session

   user@: my-ligare-app $ python -m app
   Hello, world!

   Press anything to exit.

Creating the Config Class
^^^^^^^^^^^^^^^^^^^^^^^^^

Now let's see how to create the ``Config`` class and make better use of Ligare.

Here we will see:

* How to use Ligare's dependency injection system
* How to set up application configuration with a file
* How to use configuration values from a configuration file

Start by importing Ligare's base ``Config`` class.

.. code-block:: python

   from Ligare.programming.config import Config

To create a ``Config`` class for our application, we need to extend ``Config``
and add any fields to it that we expect to be in a configuration file, and
that we want the application to be able to read.

.. code-block:: python

   class AppConfig(Config):
      message: str

Because we want to display a message from a configuration file, we just add
a "message" field to our class. We will not set this value directly; this class
is a Pydantic dataclass whose values Ligare will set from a TOML file.

Registering the Config Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Ligare to know about this class, and to tell Ligare where our configuration
file is, we use the ``use_configuration`` method from the ``ApplicationBuilder``
instance to "register" the class with Ligare's dependency injection system.
This must occur before ``builder.build()`` is called.

.. code-block:: python

   builder.use_configuration(
      lambda config_builder: config_builder \
         .with_config_type(AppConfig) \
         .with_config_filename("app/config.toml")
   )

``use_configuration`` expects to receive a method that takes a single parameter.
That parameter type is itself an ``ApplicationConfigBuilder`` that is used to set
options specific to the configuration of a Ligare application.
`It's builders all the way down! <https://en.wikipedia.org/wiki/Turtles_all_the_way_down>`_

Using the Config Class
~~~~~~~~~~~~~~~~~~~~~~

Now we need to adjust our run method.

.. code-block:: python

   class Application(ApplicationBase):
      @inject # 1
      @override
      def run(self, config: "AppConfig"): # 2
         print(config.message) # 3
         input("\nPress anything to exit. ")

There are three notable changes here:

1. The ``@inject`` decorator was added to the run method
2. The ``config`` parameter was added to the run method
3. The ``config`` object is used to print a field value called ``message``

Ligare supports the use of `Dependency Injection <https://en.wikipedia.org/wiki/Dependency_injection>`_
so you can use certain objects throughout your application without having to instantiate them yourself.
In this case, ``run(config)`` is called automatically by Ligare. Because the ``@inject`` decorator is present (#1),
the value of ``config`` is created automatically, and it is passed into your run method.

We then need to specify what the type of the parameter is (#2); in this case, the type is ``AppConfig``.
This is accomplished with Python's `type annotation <https://docs.python.org/3/library/typing.html>`_ system,
by writing ``config: "AppConfig"``.

Finally, we use the value of ``config`` to access the field ``message``, and pass that into ``print``. (#3)

With these changes, your application should resemble the Ligare example CLI application.

.. literalinclude:: ../../../../../examples/cli-app/app/__main__.py
   :language: python
   :caption: :example:`cli-app/app/__main__.py`

Creating the Application Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is one last thing to do, which is to create the configuration file and store our message in it.

.. code-block:: shell-session

   user@: my-ligare-app $  cat > app/config.toml <<EOF
   [app]
   message = "Hello, world!"
   EOF

Now we can run our application to see the message stored in the configuration file.

.. code-block:: shell-session

   user@: my-ligare-app $ python -m app
   Hello, world!

   Press anything to exit. 
