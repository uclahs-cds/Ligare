# Boutros Lab Python Libraries [ `BL_Python` ]

A collection of Python libraries for creating web applications, working with databases, writing tests, and supporting utilities.

# Quick Starts

**🚩** `BL_Python` has a minimum Python version requirement of `>= 3.10`.

*  Create a BL_Python [web application](src/web/README.md)


# Available Libraries

Following are each of the libraries in this repository.

They can be used in Python under the `BL_Python` namespace. For example, to use the database libraries you would import from `BL_Python.database`.

To use these packages during development of `BL_Python` itself, please refer to [Development](#development).

## AWS [ `BL_Python.aws` ]
Libraries for working with AWS.

Review the `BL_Python.AWS` [readme](src/AWS/README.md)

#### PyPI Package Name
`bl-python.aws`

#### Git VCS URL
`bl-python-aws@ git+ssh://git@github.com/uclahs-cds/BL_Python.git@main#subdirectory=src/AWS`

## Database [ `BL_Python.database` ]
Libraries for working with SQLite and PostgreSQL databases.

Review the `BL_Python.database` [readme](src/database/README.md)

#### PyPI Package Name
`bl-python.database`

#### Git VCS URL
`bl-python-database@ git+ssh://git@github.com/uclahs-cds/BL_Python.git@main#subdirectory=src/database`

## Development [ `BL_Python.development` ]
Utilities and tools for assisting in development of software.

Review the `BL_Python.development` [readme](src/development/README.md)

#### PyPI Package Name
`bl-python.development`

#### Git VCS URL
`bl-python-development@ git+ssh://git@github.com/uclahs-cds/BL_Python.git@main#subdirectory=src/development`

## Development [ `BL_Python.GitHub` ]
Utilities for working with the GitHub HTTP API. Uses `PyGithub` under the hood.

Review the `BL_Python.GitHub` [readme](src/GitHub/README.md)

#### PyPI Package Name
`bl-python.github`

#### Git VCS URL
`bl-python-github@ git+ssh://git@github.com/uclahs-cds/BL_Python.git@main#subdirectory=src/GitHub`

## Platform [ `BL_Python.platform` ]
Libraries for PaaS offerings such as tools for altering application configurations.

Review the `BL_Python.platform` [readme](src/platform/README.md)

#### PyPI Package Name
`bl-python.platform`

#### Git VCS URL
`bl-python-platform@ git+ssh://git@github.com/uclahs-cds/BL_Python.git@main#subdirectory=src/platform`

## Programming [ `BL_Python.programming` ]
Libraries used for writing software, such as pattern implementations so wheels don't need to be reinvented.

Review the `BL_Python.programming` [readme](src/programming/README.md)

#### PyPI Package Name
`bl-python.programming`

#### Git VCS URL
`bl-python-programming@ git+ssh://git@github.com/uclahs-cds/BL_Python.git@main#subdirectory=src/programming`

## Testing [ `BL_Python.testing` ]
Libraries used to aid in automated testing.

Review the `BL_Python.testing` [readme](src/testing/README.md)

#### PyPI Package Name
`bl-python.testing`

#### Git VCS URL
`bl-python-testing@ git+ssh://git@github.com/uclahs-cds/BL_Python.git@main#subdirectory=src/testing`

## Web [ `BL_Python.web` ]
Libraries used to building web applications.

Review the `BL_Python.web` [readme](src/web/README.md)

#### PyPI Package Name
`bl-python.web`

#### Git VCS URL
`bl-python-web@ git+ssh://git@github.com/uclahs-cds/BL_Python.git@main#subdirectory=src/web`

# Development

`BL_Python` is a mono-repo containing several independent libraries, which are noted under [Available Libraries](#available-libraries).

When developing from within the mono-repo, the libraries can be individually installed by referencing their path. Both the mono-repo and each library have their own set of dependencies.

To install the base dependencies, run `pip install -e .` from the mono-repo root. Development dependencies can be installed with `pip install -e .[dev-dependencies]`

To install the library dependencies, run, for example, `pip install -e src/web` to install `BL_Python.web`. Similar to the mono-repo, development dependencies can be installed with `pip install -e src/web[dev-dependencies]`. To install all libraries, you can run `./install_all.sh`.

## Important requirement!

Due to limitations in `pip`, some `BL_Python` libraries that depend on other `BL_Python` libraries need those dependencies explicitly defined in applications using those libraries.

The libraries that require this will outline their explicit dependencies in their respective readme files. `pip` will also show an error if these requirements are not met, which will aid in discovery of invalid dependency configurations in your software.
