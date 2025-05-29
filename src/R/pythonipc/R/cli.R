partial <- function(func, ...) {
  fixed <- list(...);
  new.func <- function() {}
  formals(new.func) <- formals(func);
  body(new.func) <- bquote({
    args <- as.list(match.call())[-1]
    do.call(.(func), modifyList(.(fixed), args))
    });
  return(new.func);
  }


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
  output.type.func <- partial(
    original.output.type.func,
    units = 'in',
    res = 96
    );

  return(c(
    output.type = output.type,
    output.type.func = output.type.func,
    output.device = output.device
    ));
  }
