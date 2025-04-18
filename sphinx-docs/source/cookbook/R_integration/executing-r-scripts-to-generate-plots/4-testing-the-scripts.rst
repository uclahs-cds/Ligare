Testing the Scripts
====================

Testing the Python Script
--------------------------

Because :class:`RProcessStepBuilder<Ligare.programming.R.process.RProcessStepBuilder>` handles
most of the R execution complexity for us, running the script is easy.

.. code-block:: shell-session

   user@: my-ligare-app $ .venv/bin/python draw_plot.py > my_img.png

Testing the R Script Without Python
------------------------------------

Python executes the equivalent of these Bash shell commands. You can do this to test
your R script in exactly the same way your Python script will.

.. code-block:: bash

   export METHOD_ARG_READ_FD=8
   export IMAGE_DATA_FD=9
   arg_read_tmpfile=$(mktemp)
   img_data_tmpfile=$(mktemp)
   exec {METHOD_ARG_READ_FD}<> "$arg_read_tmpfile"
   exec {IMAGE_DATA_FD}<> "$img_data_tmpfile"
   echo -e 'spacing,line_width,color,background_color\n1.2,6,"green","black"' >&$METHOD_ARG_READ_FD
   /usr/bin/Rscript draw_plot.R < letter_segments.csv --output-type=png

   # The image data can be written to a file with this
   cat <&$IMAGE_DATA_FD > my_img.png

Of course, you can forego any method parameters and additional file descriptor configuration.

.. code-block:: shell-session

   user@: my-ligare-app $ /usr/bin/Rscript draw_plot.R < letter_segments.csv > my_img.png
