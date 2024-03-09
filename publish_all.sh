#!/bin/bash
set -eEo pipefail

spinwait_pid=
spinwait_col=
spinwait() {
    IFS=';'
    # inspiration https://unix.stackexchange.com/a/183121
    read -sdRr -p $'\E[6n' spinwait_row spinwait_col
    spinwait_row="${spinwait_row#*[}"

    s=(\| / - \\)
    i=0
    while true; do
        tput cup $((spinwait_row-1)) "$spinwait_col" 2> /dev/null
        echo -en "  ${s[i]}"; i=$(( (i + 1) % ${#s[@]}))
        sleep 0.2
    done &
    spinwait_pid=$!
}
spinwait-stop() {
    optional_msg=$1
    kill $spinwait_pid 2> /dev/null
    tput cup $((spinwait_row-1)) "$spinwait_col" 2> /dev/null
    [ -n "$optional_msg" ] && echo -e "  $optional_msg" || echo -e "   "
}

project_name=
get-project-name() {
    # inspiration https://stackoverflow.com/a/73519411
    project_name=$(awk \
        -F' = ' \
        -v s="project" \
        -v p="name" \
        '
        # process only sections (they start with ^[ )
        /^\[/{
            gsub(/[\[\]]/, "", $1)
            f = ($1 == s)
            next
        }
        # print only the value following the ` = `
        # only for the line starting with `name = `
        NF && f && $1==p{
            gsub(/"/, "", $2)
            print $2
        }' pyproject.toml)
}

trap 'spinwait-stop' ERR
trap 'spinwait-stop; exit' SIGINT SIGTERM
initialize() {
    pip install -U build twine
}

build() {
    dir="$1"
    pushd "$dir" 1> /dev/null
    get-project-name
    echo -n "Building $project_name"
    spinwait
    rm -rf dist/
    python -m build 1> /dev/null
    spinwait-stop 'done'
    popd 1> /dev/null
}

publish() {
    set +e
    local dir="$1"
    local repository
    [ -n "$2" ] && repository="$2" || repository="testpypi"
    pushd "$dir" 1> /dev/null
    get-project-name
    echo "Publishing $project_name to $repository"
    python -m twine upload --repository "$repository" dist/*
    popd 1> /dev/null
}

declare -a packages=( \
    . \
    src/AWS \
    src/database \
    src/development \
    src/GitHub\
    src/platform \
    src/programming \
    src/testing \
    src/web
)

initialize

for package in ${packages[@]}; do
    build $package
done

# default to testpypi
[ -n "$1" ] && repository="$1" || repository="testpypi"

tput init 2> /dev/null
for package in ${packages[@]}; do
    publish $package $repository
done