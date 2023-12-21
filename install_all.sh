#!/bin/sh

# use $1 to pass in -e (or any other options)

python -m pip install $1 .

python -m pip install $1 \
    .[dev-dependencies] \
    src/AWS \
    src/database \
    src/development \
    src/GitHub \
    src/platform \
    src/programming \
    src/testing \
    src/web
