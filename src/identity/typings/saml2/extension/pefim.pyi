"""
This type stub file was generated by pyright.
"""

from saml2 import SamlBase

NAMESPACE = ...
class SPCertEncType_(SamlBase):
    """The urn:net:eustix:names:tc:PEFIM:0.0:assertion:SPCertEncType element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...
    def __init__(self, key_info=..., x509_data=..., verify_depth=..., text=..., extension_elements=..., extension_attributes=...) -> None:
        ...
    


def spcertenc_type__from_string(xml_string): # -> None:
    ...

class SPCertEnc(SPCertEncType_):
    """The urn:net:eustix:names:tc:PEFIM:0.0:assertion:SPCertEnc element"""
    c_tag = ...
    c_namespace = ...
    c_children = ...
    c_attributes = ...
    c_child_order = ...
    c_cardinality = ...


def spcertenc_from_string(xml_string): # -> None:
    ...

ELEMENT_FROM_STRING = ...
ELEMENT_BY_TAG = ...
def factory(tag, **kwargs):
    ...
