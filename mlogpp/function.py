from .value import *


class Function:
    name: str
    params: list[tuple[str, Type]]

    def __init__(self, name: str, params: list[tuple[str, Type]]):
        self.name = name
        self.params = params

    def __hash__(self):
        return hash((self.name, tuple(self.params)))
