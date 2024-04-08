"""
This type stub file was generated by pyright.
"""

from saml2 import SAMLError

logger = ...
__author__ = ...
COMMON_ARGS = ...
SP_ARGS = ...
AA_IDP_ARGS = ...
PDP_ARGS = ...
AQ_ARGS = ...
AA_ARGS = ...
COMPLEX_ARGS = ...
ALL = ...
SPEC = ...
_RPA = ...
_PRA = ...
_SRPA = ...
PREFERRED_BINDING = ...
class ConfigurationError(SAMLError):
    ...


class Config:
    def_context = ...
    def __init__(self, homedir=...) -> None:
        ...
    
    def setattr(self, context, attr, val): # -> None:
        ...
    
    def getattr(self, attr, context=...): # -> Any | None:
        ...
    
    def load_special(self, cnf, typ): # -> None:
        ...
    
    def load_complex(self, cnf): # -> None:
        ...
    
    def load(self, cnf, metadata_construction=...): # -> Self:
        """The base load method, loads the configuration

        :param cnf: The configuration as a dictionary
        :return: The Configuration instance
        """
        ...
    
    def load_file(self, config_filename, metadata_construction=...): # -> Self:
        ...
    
    def load_metadata(self, metadata_conf): # -> MetadataStore:
        """Loads metadata into an internal structure"""
        ...
    
    def endpoint(self, service, binding=..., context=...): # -> list[Any]:
        """Goes through the list of endpoint specifications for the
        given type of service and returns a list of endpoint that matches
        the given binding. If no binding is given all endpoints available for
        that service will be returned.

        :param service: The service the endpoint should support
        :param binding: The expected binding
        :return: All the endpoints that matches the given restrictions
        """
        ...
    
    def endpoint2service(self, endpoint, context=...): # -> tuple[Any, Any] | tuple[None, None]:
        ...
    
    def do_extensions(self, extensions): # -> None:
        ...
    
    def service_per_endpoint(self, context=...): # -> dict[Any, Any]:
        """
        List all endpoint this entity publishes and which service and binding
        that are behind the endpoint

        :param context: Type of entity
        :return: Dictionary with endpoint url as key and a tuple of
            service and binding as value
        """
        ...
    


class SPConfig(Config):
    def_context = ...
    def __init__(self) -> None:
        ...
    
    def vo_conf(self, vo_name): # -> None:
        ...
    
    def ecp_endpoint(self, ipaddress): # -> Any | None:
        """
        Returns the entity ID of the IdP which the ECP client should talk to

        :param ipaddress: The IP address of the user client
        :return: IdP entity ID or None
        """
        ...
    


class IdPConfig(Config):
    def_context = ...
    def __init__(self) -> None:
        ...
    


def config_factory(_type, config): # -> SPConfig | IdPConfig | Config:
    """

    :type _type: str
    :param _type:

    :type config: str or dict
    :param config: Name of file with pysaml2 config or CONFIG dict

    :return:
    """
    ...
