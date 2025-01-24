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

Now we can create a minimal ``pyproject.toml`` file that lets us create our application, and install ``Ligare.web``.

.. code-block:: shell-session

   user@: my-ligare-app $ cat > pyproject.toml << EOF
   [project]
   requires-python = ">= 3.10"

   name = "web-api"
   version = "0.0.1"

   dependencies = [
      "Ligare.web"
   ]

   EOF

Once completed, our ``pyproject.toml`` should look like this.

.. literalinclude:: ../../../../../examples/web-api/pyproject.toml
   :language: toml
   :caption: :example:`web-api/pyproject.toml`

Now we can install everything necessary to create a Ligare application.

.. note::

   We use ``-e`` here so changes to our application can run without requiring a reinstall.

.. code-block:: shell-session

   user@: my-ligare-app $ pip install -e .
