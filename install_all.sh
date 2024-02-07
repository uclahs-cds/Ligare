#!/bin/sh

# use $1 to pass in -e (or any other options)

python -m pip install $1 .[dev-dependencies]
