# Attempt to parse R values from Python values.
# Warning: this method calls `eval`. Do no use with
# untrusted data.
#' @export
parse.value <- function(x) {
  if (!is.character(x)) return(x);

  # parse the string and evaluate it.
  # this allows strings like `"c('a','b')"`
  # to become the R value `c('a', 'b')`.
  parsed <- try(eval(str2lang(x)), silent = TRUE);

  if (
    inherits(parsed, 'try-error')
    || (!is.atomic(parsed) && !is.list(parsed) && !is.null(parsed))
  )
    return(x);

  return(parsed);
}

#' @export
read.csv.as.method.parameters <- function(parameter.csv) {
  parameters <- read.csv(text = parameter.csv, header = TRUE);
  parameter.args <- as.list(parameters[1, ]);
  # Convert `None`-valued parameters that were explicitly
  # changed to `"__NULL__"` into `list(NULL)`. This makes
  # the default arg values `NULL` without removing them from
  # the list of arguments.
  # Unfortunately, the string value `"NULL"` is not implicitly
  # converted, so this is necessary to handle these default
  # values. We don't do this with `"TRUE"` or `"FALSE"`
  # because R automatically converts these values.
  # Similarly, `None` is converted to `NA`.
  parameter.args[parameter.args == '__NULL__'] <- list(NULL);

  return(lapply(parameter.args, parse.value));
}

#' @export
read.method.parameters <- function(con=NULL) {
  # Read function parameters from the METHOD_ARG_READ_FD pipe.
  # This data is written through a pipe FD from the parent
  # process (likely the cev.py endpoint API).
  if (is.null(con)) {
    fd <- as.integer(Sys.getenv('METHOD_ARG_READ_FD'));

    if (is.na(fd)) return(NULL);

    con <- file(paste0('/dev/fd/', fd), 'r', raw = TRUE);
  }
  parameter.csv <- readLines(con);
  close(con);
  method.parameters <- tryCatch(
    read.csv.as.method.parameters(parameter.csv),
    error = function(e) NULL
  );
  return(method.parameters);
}

#' @export
read.dataframe <- function(con=NULL, header = TRUE, na.strings = 'NA', ...) {
  # We read stdin like this so we can read the data more than once.
  # using just the `stdin` stream means we couldn't:
  # 1. read the first.line for `determine.file.type()`
  # 2. read the entire T/CSV for `read.csv()`
  # Read from stdin properly
  if (is.null(con)) {
    con <- file('stdin', 'r');
  }
  raw.text <- readLines(con);
  close(con);

  # attempt reading the file as a TSV first
  cev.data <- tryCatch(
    read.csv(
      text = raw.text,
      sep = '\t',
      header = header,
      na.strings = na.strings,
      ...
    ),
    error = function(e) NULL
  );

  # if the file is not a TSV (or has a single column)
  # try to load it as a CSV
  if (is.null(cev.data) || ncol(cev.data) == 1) {
    cev.data <- tryCatch(
      read.csv(
        text = raw.text,
        sep = ',',
        header = header,
        na.strings = na.strings,
        ...
      ),
      error = function(e) NULL
    );
  }

  return(cev.data);
}
