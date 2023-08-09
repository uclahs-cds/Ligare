# Boutros Lab Python Libraries [ BL_Python ]

A collection of Python libraries for creating web applications, working with databases, writing tests, and supporting utilities.

# Available Libraries

Following are each of the libraries in this repository.

They can be used in Python under the `BL_Python` namespace. For example, to use the database libraries you would import from `bl-python.database`.

## AWS [ `bl-python.aws` ]
Libraries for working with AWS.

Review the `BL_Python.AWS` [readme](src/AWS/README.md)

#### Git VCS URL
`bl-python-aws@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/AWS`

## Database [ `bl-python.database` ]
Libraries for working with SQLite and PostgreSQL databases.

Review the `BL_Python.database` [readme](src/database/README.md)

#### Git VCS URL
`bl-python-database@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/database`

## Development [ `bl-python.development` ]
Utilities and tools for assisting in development of software.

Review the `BL_Python.development` [readme](src/development/README.md)

#### Git VCS URL
`bl-python-development@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/development`

## Platform [ `bl-python.platform` ]
Libraries for PaaS offerings such as tools for altering application configurations.

Review the `BL_Python.platform` [readme](src/platform/README.md)

#### Git VCS URL
`bl-python-platform@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/platform`

## Programming [ `bl-python.programming` ]
Libraries used for writing software, such as pattern implementations so wheels don't need to be reinvented.

Review the `BL_Python.programming` [readme](src/programming/README.md)

#### Git VCS URL
`bl-python-programming@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/programming`

## Testing [ `bl-python.testing` ]
Libraries used to aid in automated testing.

Review the `BL_Python.testing` [readme](src/testing/README.md)

#### Git VCS URL
`bl-python-testing@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/testing`

## Web [ `bl-python.web` ]
Libraries used to building web applications.

Review the `BL_Python.web` [readme](src/web/README.md)

#### Git VCS URL
`bl-python-web@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/web`

# Using BL_Python in your projects

Currently these libraries are not available in any package repository, and so much be imported via other means.

The suggested method is to use the `git+ssh` [VCS URL](https://pip.pypa.io/en/stable/topics/vcs-support/) with `pip`.

As an example, include the `BL_Python.programming` library like this within `pyproject.toml`:

```toml
[project]
dependencies = [
    bl-python-programming@ git+ssh://git@github.com/uclahs-cds/private-BL-python-libraries.git@main#subdirectory=src/programming
]
```

Make note of the following:
* The library name is prefixed with `bl-python-` followed by the library name, which is `programming` in this example. This is due to how Python namespaces packages, and the pattern is necessary for the other libraries as well.
* The Git URL is followed by `@`, then `main`. Use this if you want the _unstable_ features in the `main` Git branch. Any Git [ref](https://git-scm.com/book/en/v2/Git-Internals-Git-References) can be used, which is helpful to lock the dependency to a specific version. The `@` is always needed when specifying a ref.
* The Git URL ends with `#subdirectory=BL_Python/programming`. This is necessary to specify that the dependency `bl-python-programming` exists at `src/programming`.

## Important requirement!

Due to limitations in `pip`, some `BL_Python` libraries that depend on other `BL_Python` libraries need those dependencies explicitly defined in applications using those libraries.

The libraries that require this will outline their explicit dependencies in their respective readme files. `pip` will also show an error if these requirements are not met, which will aid in discovery of invalid dependency configurations in your applications.