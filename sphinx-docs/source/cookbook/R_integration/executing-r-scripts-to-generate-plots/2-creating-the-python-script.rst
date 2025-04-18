.. toctree::
   :maxdepth: 2
   :caption: Contents:

Creating the Python Script
---------------------------

Now that we're set up to create a Ligare application, let's see how to integrate an R script into it.

For the purpose of this guide, we're going to create a single Python Script and a single R script.
The R script will read in method arguments and data, then output a plot.

Our final Python script will look like this.

.. literalinclude:: ../../../../../examples/R-integration/draw_plot.py
   :language: python
   :caption: :example:`draw_plot.py`

Using ``RProcessStepBuilder``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The main point of integration is :class:`RProcessStepBuilder<Ligare.programming.R.process.RProcessStepBuilder>`.

.. note::

   A `Step Builder <https://refactoring.guru/design-patterns/builder>`_ is a design pattern to help configure an object.
   In this case, :class:`RProcessStepBuilder<Ligare.programming.R.process.RProcessStepBuilder>` configures the ``Rscript`` command
   needed to execute an R script.

Let's start with configuring the ``Rscript`` executable.

.. code-block:: python

   r_process_builder = RProcessStepBuilder()
   r_process_script_builder = r_process_builder \
      .with_Rscript_binary_path("/usr/bin/Rscript")

By doing this, we're telling the builder where the ``Rscript`` executable is. This
is the command that will execute your R script.

.. note::

   If ``/usr/bin/Rscript`` does not exist on your system,
   replace the value with the path to your ``Rscript`` command.

Next, we will configure options for the R script itself.

.. code-block:: python

   r_script_method_builder = r_process_script_builder \
      .with_args(["--output-type=png"]) \
      .with_R_script_path("draw_plot.R")

This creates a command that is equiavlent to ``/usr/bin/Rscript draw_plot.R --output-type=png``

With the R script path and commandline options configured, we now need to configure
the method that the R script executes to draw a plot.

.. code-block:: python

   r_executor_builder = r_script_method_builder \
      .with_method_parameters({
         "spacing": 1.2,
         "line_width": 6,
         "color": "green",
         "background_color": "black",
      }) \
      .with_data(data) # we will read data from a CSV

With the R script that we will write, this causes the R script to execute the equivalent of this.

.. code-block:: R

   draw_lines_from_dataframe(
      data,
      spacing=1.2,
      line_width=6,
      color="green",
      background_color="black"
   )

Reading and Writing Data
~~~~~~~~~~~~~~~~~~~~~~~~~~

The R script we will write expects to receive a CSV that will be parsed into a dataframe.

For this example, you can use the :example:`R-integration/letter_segments.csv` CSV.

We'll need to read this CSV file in the Python script. This is the value of ``data`` that
we used for ``with_data(data)``.

.. code-block:: python

   with open(Path(exec_dir, "letter_segments.csv"), "rb") as f:
      data = f.read()

And lastly, our R script writes PNG data to its STDOUT, which means Python needs to
read that data and pass it along to its own STDOUT. We also need to wrap up our Python
script by executing the R script.

.. code-block:: python

   (proc, img_data) = r_executor_builder.execute()
   _ = sys.stdout.buffer.write(img_data)
   _ = sys.stdout.buffer.flush()
