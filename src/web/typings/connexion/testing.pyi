"""
This type stub file was generated by pyright.
"""

from starlette.types import Receive, Scope
from connexion.operations import AbstractOperation

class TestContext:
    __test__ = ...
    def __init__(self, *, context: dict = ..., operation: AbstractOperation = ..., receive: Receive = ..., scope: Scope = ...) -> None:
        ...
    
    def __enter__(self) -> None:
        ...
    
    def __exit__(self, type, value, traceback): # -> Literal[False]:
        ...
    
    @staticmethod
    def build_context() -> dict:
        ...
    
    @staticmethod
    def build_operation() -> AbstractOperation:
        ...
    
    @staticmethod
    def build_receive() -> Receive:
        ...
    
    @staticmethod
    def build_scope(**kwargs) -> Scope:
        ...
    


