"""
This type stub file was generated by pyright.
"""

from connexion.resolver import Resolver

"""
This module contains a mock resolver that returns mock functions for operations it cannot resolve.
"""
logger = ...
class MockResolver(Resolver):
    def __init__(self, mock_all) -> None:
        ...
    
    def resolve(self, operation): # -> Resolution:
        """
        Mock operation resolver

        :type operation: connexion.operations.AbstractOperation
        """
        ...
    
    def mock_operation(self, operation, *args, **kwargs): # -> tuple[Any, Any] | tuple[Literal['No example response was defined.'], Any]:
        ...
    


