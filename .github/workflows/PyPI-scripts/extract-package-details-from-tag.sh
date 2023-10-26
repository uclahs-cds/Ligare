#!/bin/bash
set -eo pipefail
tag="${GITHUB_REF#refs/*/}"

# This is the package name minus `BL_Python.`.
package_name=$(gawk 'match($0, /BL_Python\.?([^-]+)?/, m) { print s m[1]}' <<<$tag)
# `all` is the root of the repository and includes all other packages
if [ "$package_name" == "all" ]; then
    package_directory=.
else
    package_directory="src/$package_name/"
fi
echo "package_name=$package_name" >> $GITHUB_OUTPUT
echo "package_directory=$package_directory" >> $GITHUB_OUTPUT