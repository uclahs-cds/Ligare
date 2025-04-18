.. toctree::
   :maxdepth: 2
   :caption: Contents:

Creating the R Script
----------------------

With our Python script completed, we now need to create the R script that it will execute.

This R script is responsible for receiving CSV data and method arguments from Python,
and writing a plot as image data to STDOUT.

Our final R script will look like this.

.. literalinclude:: ../../../../../examples/R-integration/draw_plot.R
   :language: R
   :caption: :example:`draw_plot.R`

Using ``pythonipc``
^^^^^^^^^^^^^^^^^^^^

Ligare contains an R package named :source:`pythonipc <src/R/pythonipc>`. This package
contains utility methods for working with R script executions performed by :class:`RProcessStepBuilder<Ligare.programming.R.process.RProcessStepBuilder>`.

We will use ``pythonipc`` to execute an R script from through Python, which
will draw line segments to a plot and then return a PNG.

Let's start with some initial output device configuration, and reading the commandline
options specified by Python.

First, we prevent the default PDF output from occurring. We also tell R to clean up
output devices when the script exits for any reason.

.. code-block:: R

   on.exit(dev.off(), add = TRUE);
   invisible(pdf(NULL));


Next, we read in the commandline arguments.

.. code-block:: R

   library("pythonipc");

   with(as.list(parse.cli.args()), {
      invisible(output.type.func(output.device));
   })

``pythonipc`` contains a method named :source:`parse.cli.args <src/R/pythonipc/R/cli.R#L2>`.

This method returns commandline argument values. Here, we use ``output.type.func`` and ``output.device``.
:class:`RProcessStepBuilder<Ligare.programming.R.process.RProcessStepBuilder>` creates these for us,
although we configured ``output.type.func`` using ``with_args(["--output-type=png"])``.
The value here is the R output device function matching the commandline value - in our case, it is `png <https://www.rdocumentation.org/packages/grDevices/versions/3.4.1/topics/png>`_.

``output.device`` is the file descriptor that R will write image data to. By default, this is ``"/dev/stdout"``,
but :class:`RProcessStepBuilder<Ligare.programming.R.process.RProcessStepBuilder>` handles this a bit differently. In general,
it is enough to be aware of this and to call ``output.type.func(output.device)``.

Now we will read the method parameters we configured using ``with_method_parameters(...)``.

.. code-block:: R

   parameter_args <- read.method.parameters();

And then we read the line segment data we configured using ``with_data(data)``

.. code-block:: R

   letter_segments <- read.dataframe();

This is all that is necessary to receive the configured command parameters that Python executed.

The last thing to do is to apply the values, and execute the method.

.. code-block:: R

   do.call(draw_lines_from_dataframe, c(list(letter_segments), parameter_args));
