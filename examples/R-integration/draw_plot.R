# nolint start: commented_code_linter.
library("pythonipc");

# This method takes in a set of coordinates from a dataframe
# and draws those coordinates as line segments.
# For example, the letter "L" would be stored like this.
# letter_segments <- data.frame(
#  letter = c("L", "L"),
#  x = c(0.0, 0.0),
#  y = c(0.0, 0.0),
#  xend = c(0.0, 0.6),
#  yend = c(1.0, 0.0)
# )
draw_lines_from_dataframe <- function(df, spacing = 1, line_width = 1,
                                      color = "black",
                                      background_color = "white") {
  par(bg = background_color);
  plot(NULL, xlim = c(0, 7), ylim = c(0, 1.1), asp = 1, axes = FALSE, xlab = "",
       ylab = "");

  unique_letters <- unique(df$letter);
  for (i in seq_along(unique_letters)) {
    current_letter <- unique_letters[i];
    letter_data <- subset(df, df$letter == current_letter);
    segments(
      letter_data$x + (i - 1) * spacing, letter_data$y,
      letter_data$xend + (i - 1) * spacing, letter_data$yend,
      lwd = line_width,
      col = color
    );
  }
}

on.exit(dev.off(), add = TRUE);

invisible(pdf(NULL));

# get the output format and data FDs
with(as.list(parse.cli.args()), {
  invisible(output.type.func(output.device));
})

# read the method parameters for `draw_lines_from_dataframe`
parameter_args <- read.method.parameters();
# read the line segment data for `draw_lines_from_dataframe`
letter_segments <- read.dataframe();

# apply the line segment dataframe and other parameters
# to the `draw_lines_from_dataframe` method
do.call(draw_lines_from_dataframe, c(list(letter_segments), parameter_args));

# nolint end
