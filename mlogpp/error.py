import enum

from .formatting import Format
from .util import Position, sanitize


class MlogError(Exception):
    def __init__(self, msg: str, pos: Position = None):
        self.message = f"{msg}: {pos}"

        self.msg = msg
        self.pos = pos
    
    def print(self):
        if self.pos is not None:
            print(f"{Format.ERROR}{Format.BOLD}Error{Format.RESET}{Format.ERROR} in file {self.pos.file} on line {self.pos.line}, column {self.pos.start+1}: {self.msg}{Format.RESET}")
            print(f"Here:\n{self.pos.code}\n{self.pos.arrows()}")
        else:
            print(f"{Format.ERROR}{Format.BOLD}Error{Format.RESET}{Format.ERROR}: {self.msg}{Format.RESET}")


class Error:
    @staticmethod
    def unexpected_character(pos: Position, ch: str):
        raise MlogError(f"Unexpected character [{ch}]", pos)

    @staticmethod
    def already_imported(pos: Position, path: str):
        raise MlogError(f"Already imported [{path}]", pos)

    @staticmethod
    def cannot_find_file(pos: Position, path: str):
        raise MlogError(f"Cannot find file [{path}]", pos)

    @staticmethod
    def unexpected_token(tok: 'Token'):
        raise MlogError(f"Unexpected token [{sanitize(tok.value)}]", tok.pos)

    @staticmethod
    def unexpected_eof(pos: Position):
        raise MlogError(f"Unexpected EOF", pos)

    @staticmethod
    def incompatible_types(node: 'Node', a: 'Type', b: 'Type'):
        raise MlogError(f"Incompatible types [{a.name}, {b.name}]", node.get_pos())

    @staticmethod
    def undefined_function(node: 'Node', func: str):
        raise MlogError(f"Undefined function [{func}]", node.get_pos())

    @staticmethod
    def already_defined_var(node: 'Node', name: str):
        raise MlogError(f"Variable [{name}] is already defined", node.get_pos())

    @staticmethod
    def undefined_variable(node: 'Node', name: str):
        raise MlogError(f"Undefined variable [{name}]", node.get_pos())

    @staticmethod
    def invalid_arg_count(node: 'Node', count: int, expected: int):
        raise MlogError(f"Invalid number of arguments to function ({count}, expected {expected})", node.get_pos())

    @staticmethod
    def write_to_const(node: 'Node', var: str):
        raise MlogError(f"Trying to write into a constant [{var}]", node.get_pos())
