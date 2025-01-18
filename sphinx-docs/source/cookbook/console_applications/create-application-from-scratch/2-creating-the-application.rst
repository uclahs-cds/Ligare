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
   user@: my-ligare-app $ touch app/__init__.py app/__main__.py

Now we need to add some code to ``__main__.py``.

First, let's add some imports that our application depends on.

.. code-block:: python

   from injector import inject
   from Ligare.programming.application import ApplicationBase, ApplicationBuilder
   from Ligare.programming.config import Config
   from typing_extensions import override

We're going to write an application that displays a message stored in a configuration file.

To do this, we need to do a few things:

1. Create an ``Application`` class
2. Create a ``Config`` class
3. Configure the application

Creating the Application Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All Ligare applications are extensions of ``ApplicationBase``. These classes must implement a ``run`` method, which can use the Ligare dependency injection system.

For our console application, we're going to print a message from an instance of a ``Config`` class.

.. code-block:: python

   class Application(ApplicationBase):
      @inject
      @override
      def run(self, config: "AppConfig"):
         print(config.message)
         input("\nPress anything to exit. ")

Here, we have created a class called ``Application`` that extends ``ApplicationBase``.
We then implement the run method with a single parameter named ``config``. The use of
``@inject`` ensures that the run method receives an instance of ``AppConfig`` as the
value of ``config``.

There is no need to instantiate ``Application``, no need to call ``run``, and no need
to pass in the value of ``config`` ourselves - Ligare will do this for us.

To set up Ligare to run our application, we will use ``ApplicationBuilder``.

.. code-block:: python

   builder = ApplicationBuilder(Application)

This gives us a builder for our ``Application`` class with which we can configure the
application, and then start it. While there are a variety of options we can set,
this guide will only go over ``use_configuration``.

.. code-block:: python

   class AppConfig(Config):
      message: str

   builder.use_configuration(
      lambda config_builder: config_builder \
         .with_config_type(AppConfig) \
         .with_config_filename("app/config.toml")
   )

``use_configuration`` expects to receive a method that takes a single parameter.
That parameter type is itself an ``ApplicationConfigBuilder`` that is used to set
options specific to the configuration of a Ligare application.
`It's builders all the way down! <https://en.wikipedia.org/wiki/Turtles_all_the_way_down>`_

First we create our ``Config`` class, ``AppConfig``. This class is a Pydantic dataclass
whose values Ligare will set from a TOML file.

Then, within the function passed to ``use_configuration``, we set both the type of our
config class, and the path to the TOML file.

This is the minimum required to set up our application. We can now "build" it,
and then start it.


.. code-block:: python

   application = builder.build()

   if __name__ == "__main__":
      application.run()



.. First, ``Ligare.web`` uses a `builder <https://en.wikipedia.org/wiki/Builder_pattern>`_ to set up an instance of your application during runtime.
.. This allows us to `build` our application using specific functions to configure desired beavhiors and features.
.. 
.. .. seealso::
.. 
..    A `builder <https://en.wikipedia.org/wiki/Builder_pattern>`_ is a pattern that helps programmers configure an instance of some other `type`.
..    For this guide, it helps us configure an instance of ``FlaskApp``, which is the
..    class name for the type of application we're creating.
.. 
.. 
.. The class we need for this is :obj:`ApplicationBuilder[T] <Ligare.web.application.ApplicationBuilder>`. We also need the application type. For this example, we're using `FlaskApp <https://github.com/spec-first/connexion/blob/3450a602fdd43b1d3a06581fd0106397b32e965b/connexion/apps/flask.py#L166>`_.
.. 
.. .. seealso::
.. 
..    A "generic" class is a way to specify `generic` functionality for a range of more specific types.
..    Here, we use the generic class :obj:`ApplicationBuilder[T] <Ligare.web.application.ApplicationBuilder>` to configure `generic` aspects of
..    ``FlaskApp``.
..    Here, the "generic type" is named ``T`` and is how we reference the more specific type that
..    it represents.
.. 
..    .. note:: 
.. 
..       :obj:`ApplicationBuilder[T] <Ligare.web.application.ApplicationBuilder>` supports one other type of class called ``Flask``.
..       Review `this guide <it doesn't exist yet>`_ to see how to create a ``Flask`` application.

.. literalinclude:: ../../../../../examples/cli-app/app/__main__.py
   :language: python
   :caption: :example:`cli-app/app/__main__.py`

Now we have something we can run. Go ahead and run this code.

.. code-block:: shell-session

   user@: my-ligare-app $ python -m app
