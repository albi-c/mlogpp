from .value import *


class Function:
    name: str
    params: list[tuple[str, Type]]
    return_type: Type

    def __init__(self, name: str, params: list[tuple[str, Type]], return_type: Type):
        self.name = name
        self.params = params
        self.return_type = return_type

    def __hash__(self):
        return hash((self.name, tuple(self.params), self.return_type))
