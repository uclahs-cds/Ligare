#!/bin/sh

# use $1 to pass in -e (or any other options)
# if $1 is "cicd" then specific packages are installed

if [ "$1" = "cicd" ]; then
    python -m pip install .[dev-dependencies]
    python -m pip install src/database[postgres-binary]
else
    python -m pip install $1 .[dev-dependencies]
fi
