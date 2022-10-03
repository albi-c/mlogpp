import enum

from .formatting import Format
from .util import Position, sanitize


class Error(Exception):
    """
    Compilation error.
    """

    msg: str
    pos: Position | None

    def __init__(self, msg: str, pos: Position | None = None):
        """
        Args:
            msg: The message to be displayed.
            pos: Position at which the error occurred.
        """

        self.message = f"{msg}: {pos}"

        self.msg = msg
        self.pos = pos

    def print(self):
        """
        Print the error message and position.
        """

        if self.pos is not None:
            print(
                f"{Format.ERROR}{Format.BOLD}Error{Format.RESET}{Format.ERROR} in file {self.pos.file} on line {self.pos.line}, column {self.pos.start + 1}: {self.msg}{Format.RESET}")
            print(f"Here:\n{self.pos.code}\n{self.pos.arrows()}")
        else:
            print(f"{Format.ERROR}{Format.BOLD}Error{Format.RESET}{Format.ERROR}: {self.msg}{Format.RESET}")

    @staticmethod
    def unexpected_character(pos: Position, ch: str):
        raise Error(f"Unexpected character [{ch}]", pos)

    @staticmethod
    def already_imported(pos: Position, path: str):
        raise Error(f"Already imported [{path}]", pos)

    @staticmethod
    def cannot_find_file(pos: Position, path: str):
        raise Error(f"Cannot find file [{path}]", pos)

    @staticmethod
    def unexpected_token(tok: 'Token'):
        raise Error(f"Unexpected token [{sanitize(tok.value)}]", tok.pos)

    @staticmethod
    def unexpected_eof(pos: Position):
        raise Error(f"Unexpected EOF", pos)

    @staticmethod
    def incompatible_types(node: 'Node', a: 'Type', b: 'Type'):
        raise Error(f"Incompatible types [{a.name}, {b.name}]", node.get_pos())

    @staticmethod
    def undefined_function(node: 'Node', func: str):
        raise Error(f"Undefined function [{func}]", node.get_pos())

    @staticmethod
    def already_defined_var(node: 'Node', name: str):
        raise Error(f"Variable [{name}] is already defined", node.get_pos())

    @staticmethod
    def undefined_variable(node: 'Node', name: str):
        raise Error(f"Undefined variable [{name}]", node.get_pos())

    @staticmethod
    def invalid_arg_count(node: 'Node', count: int, expected: int):
        raise Error(f"Invalid number of arguments to function ({count}, expected {expected})", node.get_pos())

    @staticmethod
    def write_to_const(node: 'Node', var: str):
        raise Error(f"Trying to write into a constant [{var}]", node.get_pos())


class InternalError(Exception):
    """
    Internal compilation error.
    """

    @staticmethod
    def invalid_arg_count(ins: str, count: int, expected: int):
        raise InternalError(f"Invalid number of arguments to instruction [{ins}] ({count}, expected {expected})")

    @staticmethod
    def undefined_function(name: str):
        raise InternalError(f"Undefined function [{name}]")
