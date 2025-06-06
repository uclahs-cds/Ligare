#' Partially apply parameter values to a method
#' and get a new method.
#'
#' @param func The function to apply parameters to.
#' @param ... Any named parameters and their values to apply to the function.
#'
#' @return A function whose parameters include the parameters from `func`
#'         whose named parameters match those in `...`.
partial <- function(func, ...) {
  fixed <- list(...);
  new.func <- function() {
  }
  formals(new.func) <- modifyList(formals(func), fixed);
  body(new.func) <- bquote({
    args <- as.list(match.call())[-1]
    do.call(.(func), modifyList(.(fixed), args))
    });
  return(new.func);
  }


#' Parse specific command-line parameters.
#'
#' `--output-type=<value>` The value of this parameter should be an
#'                         output device.
#'                         Defaults to `png`
#'
#' `--output-fd=<value>` The integer value of the file descriptor that
#'                       the output device will write to.
#'                       If not specified, `parse.cli.args` tries to get
#'                       the FD from the `IMAGE_DATA_FD` envvar.
#'                       If the envvar is not specified, this defaults
#'                       to STDOUT.
#'
#' @return A vector containing:
#' \describe{
#'   \item{output.type}{The type name of the output device, e.g., "png".}
#'   \item{output.type.func}{The function matching the
#' name of the output device. The device forces the use of
#' inches for resolution units, with a DPI of 96.}
#'   \item{output.device}{The output device name.}
#' }
#' @export
parse.cli.args <- function() {
  args <- commandArgs(trailingOnly = TRUE);

  output.type.arg <- args[grep('--output-type=', args)];
  output.type <- ifelse(
    identical(output.type.arg, character(0)),
    'png',
    sub('.*=', '', args)
  );

  get.output.device.from.env <- function(.) {
    tryCatch({
        output.fd.env <- as.integer(Sys.getenv('IMAGE_DATA_FD'));
        if (is.na(output.fd.env)) stop('NA');
        return(paste0('/dev/fd/', output.fd.env));
        },
      # envvar is not set, use stdout
      warning = function(e) '/dev/stdout',
      error = function(e) '/dev/stdout'
      );
    }

  get.output.device.from.args <- function(.) {
    tryCatch({
        output.fd.arg.value <- as.integer(sub('.*=', '', output.fd.arg));
        if (is.na(output.fd.arg.value)) stop('NA');
        return(paste0('/dev/fd/', output.fd.arg.value));
        },
      # failed to parse the arg, try to get from env
      warning = get.output.device.from.env,
      error = get.output.device.from.env
      );
    }

  output.fd.arg <- args[grep('--output-fd=', args)];
  output.device <- ifelse(
    identical(output.fd.arg, character(0)),
    get.output.device.from.env(),
    get.output.device.from.args()
    );

  original.output.type.func <- get(output.type, mode = 'function');
  original.formals <- formals(original.output.type.func);
  output.type.func <- partial(
    original.output.type.func,
    units = 'in',
    res = 96,
    width = original.formals$width / 96,
    height = original.formals$height / 96
    );

  return(c(
    output.type = output.type,
    output.type.func = output.type.func,
    output.device = output.device
    ));
  }
