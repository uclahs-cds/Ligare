library("pythonipc");

args <- parse.cli.args();
output.type.func <- args$output.type.func;

parameter.args <- read.method.parameters();
letter_segments <- read.dataframe();

on.exit(dev.off(), add = TRUE);

invisible(pdf(NULL));
invisible(output.type.func(args$output.device));

letter_segments <- read.csv("letter_segments.csv");

draw_ligare <- function(df, spacing = 1, line_width = 1, color = "black", background_color = "white") {
  par(bg = background_color);
  plot(NULL, xlim = c(0, 7), ylim = c(0, 1.1), asp = 1, axes = FALSE, xlab = "", ylab = "");
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

do.call(draw_ligare, c(list(letter_segments), parameter.args));
