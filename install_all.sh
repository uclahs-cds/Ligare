#!/bin/sh

python -m pip install -e .

python -m pip install -e \
    .[dev-dependencies] \
    src/AWS \
    src/database \
    src/development \
    src/platform \
    src/programming \
    src/testing \
    src/web
