#!/bin/bash
set -eo pipefail
tag="${GITHUB_REF#refs/*/}"

# This is the package name minus `Ligare.`.
package_name="$(gawk 'match($0, /Ligare\.?([^-]+)?/, m) { print s m[1]}' <<<"$tag")"
module_version="$(gawk 'match($0, /Ligare\.?[^v]+v(.+)/, m) { print s m[1]}' <<<"$tag")"
module_name="Ligare.$package_name"

# `all` is the root of the repository and includes all other packages
if [ "$package_name" == "all" ]; then
    package_directory=.
else
    package_directory="src/$package_name/"
fi
echo "package_name=$package_name" >> "$GITHUB_OUTPUT"
echo "package_directory=$package_directory" >> "$GITHUB_OUTPUT"
echo "module_name=$module_name" >> "$GITHUB_OUTPUT"
echo "module_version=$module_version" >> "$GITHUB_OUTPUT"
