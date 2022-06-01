from .util import Position

class Node:
    """
    base node class
    """

    def __init__(self, pos: Position):
        self.pos = pos

class CodeListNode:
    """
    node with a list of code
    """

    def __init__(self, pos: Position, code: list):
        super().__init__(pos)
        
        self.code = code
