.. toctree::
   :maxdepth: 2
   :caption: Contents:

Setting Up Your Project
------------------------

First we need to prepare a Python project. We will use a Python `virtual environment <https://docs.python.org/3/library/venv.html>`_, and the project configuration file `pyproject.toml <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>`_.

.. important:: 

   Ligare requires a minimum Python version of 3.10.

Create a project directory, create a new virtual environment, and activate the virtual environment.

.. code-block:: shell-session

   user@: $ mkdir my-ligare-app && cd my-ligare-app
   user@: my-ligare-app $ python -m venv .venv
   user@: my-ligare-app $ . .venv/bin/activate

The following commands are executed with the virtual environment activated.

Now we can create a minimal ``pyproject.toml`` file that let's us create our application, and install ``Ligare.web``.

First we need to ensure compatibility with Python 3.10.

.. code-block:: shell-session

   user@: my-ligare-app $ cat > pyproject.toml << EOF
   [project]
   requires-python = ">= 3.10"

   EOF

Next we set the name of our application.

.. code-block:: shell-session

   user@: my-ligare-app $ echo 'name = "my-ligare-app"' >> pyproject.toml

Then we set an initial version.

.. code-block:: shell-session

   user@: my-ligare-app $ echo 'version = "0.0.1"' >> pyproject.toml

Finally, we include ``Ligare.web`` as a dependency of our application.

.. code-block:: shell-session

   user@: my-ligare-app $ cat >> pyproject.toml << EOF

   dependencies = [
      "Ligare.web"
   ]
   EOF

Once completed, our ``pyproject.toml`` should look like this.

.. code-block:: toml

   [project]
   requires-python = "3.10"

   name = "my-ligare-app"
   version = "0.0.1"

   dependencies = [
      "Ligare.web"
   ]

Now we can install everything necessary to create a Ligare application.

.. code-block:: shell-session

   user@: my-ligare-app $ pip install -e .

We use ``-e`` here because this allows the application to run our changes to code without requiring that we reinstall the application every time we change something.
