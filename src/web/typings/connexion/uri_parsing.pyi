"""
This type stub file was generated by pyright.
"""

import abc

"""
This module defines URIParsers which parse query and path parameters according to OpenAPI
serialization rules.
"""
logger = ...
QUERY_STRING_DELIMITERS = ...
class AbstractURIParser(metaclass=abc.ABCMeta):
    parsable_parameters = ...
    def __init__(self, param_defns, body_defn) -> None:
        """
        a URI parser is initialized with parameter definitions.
        When called with a request object, it handles array types in the URI
        both in the path and query according to the spec.
        Some examples include:
        - https://mysite.fake/in/path/1,2,3/            # path parameters
        - https://mysite.fake/?in_query=a,b,c           # simple query params
        - https://mysite.fake/?in_query=a|b|c           # various separators
        - https://mysite.fake/?in_query=a&in_query=b,c  # complex query params
        """
        ...
    
    @property
    @abc.abstractmethod
    def param_defns(self): # -> None:
        """
        returns the parameter definitions by name
        """
        ...
    
    @property
    @abc.abstractmethod
    def param_schemas(self): # -> None:
        """
        returns the parameter schemas by name
        """
        ...
    
    def __repr__(self): # -> str:
        """
        :rtype: str
        """
        ...
    
    @abc.abstractmethod
    def resolve_form(self, form_data): # -> None:
        """Resolve cases where form parameters are provided multiple times."""
        ...
    
    @abc.abstractmethod
    def resolve_query(self, query_data): # -> None:
        """Resolve cases where query parameters are provided multiple times."""
        ...
    
    @abc.abstractmethod
    def resolve_path(self, path): # -> None:
        """Resolve cases where path parameters include lists"""
        ...
    
    def resolve_params(self, params, _in): # -> dict[Any, Any]:
        """
        takes a dict of parameters, and resolves the values into
        the correct array type handling duplicate values, and splitting
        based on the collectionFormat defined in the spec.
        """
        ...
    


class OpenAPIURIParser(AbstractURIParser):
    style_defaults = ...
    @property
    def param_defns(self): # -> dict[Any, Any]:
        ...
    
    @property
    def form_defns(self): # -> dict[Any, Any]:
        ...
    
    @property
    def param_schemas(self): # -> dict[Any, Any]:
        ...
    
    def resolve_form(self, form_data):
        ...
    
    def resolve_query(self, query_data): # -> dict[Any, Any]:
        ...
    
    def resolve_path(self, path_data): # -> dict[Any, Any]:
        ...
    


class Swagger2URIParser(AbstractURIParser):
    """
    Adheres to the Swagger2 spec,
    Assumes that the last defined query parameter should be used.
    """
    parsable_parameters = ...
    @property
    def param_defns(self): # -> dict[Any, Any]:
        ...
    
    @property
    def param_schemas(self): # -> dict[Any, Any]:
        ...
    
    def resolve_form(self, form_data): # -> dict[Any, Any]:
        ...
    
    def resolve_query(self, query_data): # -> dict[Any, Any]:
        ...
    
    def resolve_path(self, path_data): # -> dict[Any, Any]:
        ...
    


class FirstValueURIParser(Swagger2URIParser):
    """
    Adheres to the Swagger2 spec
    Assumes that the first defined query parameter should be used
    """
    ...


class AlwaysMultiURIParser(Swagger2URIParser):
    """
    Does not adhere to the Swagger2 spec, but is backwards compatible with
    connexion behavior in version 1.4.2
    """
    ...

