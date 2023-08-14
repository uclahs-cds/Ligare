# `BL_Python.web`

Libraries for building web applications in Boutros Lab.

## To Use

- set the envvar FLASK_APP
- set the envvar FLASK_SECRET_KEY

### With Connexion
If using Connexion and OpenAPI

- set the envvar OPENAPI_SPEC_PATH to the location of the OpenAPI YAML

### Without Connexion
- store Flask Blueprints under blueprints/
- postfix your blueprint variable name with `_blueprint`