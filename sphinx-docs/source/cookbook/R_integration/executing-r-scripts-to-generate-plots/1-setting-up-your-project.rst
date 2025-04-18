.. toctree::
   :maxdepth: 2
   :caption: Contents:

Setting Up Your Project
------------------------

.. important::

   Successfully following this guide requires that your system has R installed with PNG support.

.. important:: 

   Ligare requires a minimum Python version of 3.10.

Create a project directory, create a new virtual environment, and activate the virtual environment.

.. code-block:: shell-session

   user@: $ mkdir my-ligare-app && cd my-ligare-app
   user@: my-ligare-app $ python -m venv .venv
   user@: my-ligare-app $ . .venv/bin/activate

The following commands are executed with the virtual environment activated.

Now we can create a minimal ``pyproject.toml`` file that lets us create our application, and install ``Ligare.programming``.

.. code-block:: shell-session

   user@: my-ligare-app $ cat > pyproject.toml << EOF
   [project]
   requires-python = ">= 3.10"

   name = "R-integration"
   version = "0.0.1"

   dependencies = [
      "Ligare.programming"
   ]

   EOF

Once completed, our ``pyproject.toml`` should look like this.

.. literalinclude:: ../../../../../examples/R-integration/pyproject.toml
   :language: toml
   :caption: :example:`R-integration/pyproject.toml`

Now we can install everything necessary to create a Ligare application.

.. note::

   We use ``-e`` here so changes to our application can run without requiring a reinstall.

.. code-block:: shell-session

   user@: my-ligare-app $ pip install -e .
