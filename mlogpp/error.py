from __future__ import annotations

from .formatting import Format
from .util import Position, sanitize


class Error(Exception):
    """
    Compilation error.
    """

    msg: str
    pos: Position | None

    node_class: type[Node] = None

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
                f"{Format.ERROR}{Format.BOLD}Error{Format.RESET}{Format.ERROR} in file {self.pos.file} on line {self.pos.line + 1}, column {self.pos.start + 1}: {self.msg}{Format.RESET}")
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
    def unexpected_token(tok: Token):
        raise Error(f"Unexpected token [{sanitize(tok.value)}]", tok.pos)

    @staticmethod
    def unexpected_eof(pos: Position):
        raise Error(f"Unexpected EOF", pos)

    @staticmethod
    def undefined_type(node: Node, type_: str):
        raise Error(f"Undefined type [{type_}]", node.get_pos())

    @staticmethod
    def incompatible_types(node: Node, a: Type, b: Type):
        raise Error(f"Incompatible types {a}, {b}", node.get_pos())

    @staticmethod
    def private_type(node: Node, type_: Type):
        raise Error(f"Inferring private type {type_}", node.get_pos())

    @staticmethod
    def invalid_operation(node: Node, a: Value, op: str, b: Value = None):
        if b is None:
            raise Error(f"Invalid operation [{op}{a}]", node.get_pos())

        raise Error(f"Invalid operation [{a} {op} {b}]", node.get_pos())

    @staticmethod
    def not_callable(node: Node, val: Value):
        raise Error(f"Not callable [{val}]", node.get_pos())

    @staticmethod
    def already_defined_var(node: Node, name: str):
        raise Error(f"Variable [{name}] is already defined", node.get_pos())

    @staticmethod
    def already_defined_type(node: Node, name: str):
        raise Error(f"Type [{name}] is already defined", node.get_pos())

    @staticmethod
    def undefined_variable(node: Node, name: str):
        raise Error(f"Undefined variable [{name}]", node.get_pos())

    @staticmethod
    def undefined_attribute(node: Node, name: str, val: Value):
        raise Error(f"Undefined attribute [{name}] in [{val}]", node.get_pos())

    @staticmethod
    def invalid_arg_count(node: Node, count: int, expected: int):
        raise Error(f"Invalid number of arguments to function ({count}, expected {expected})", node.get_pos())

    @staticmethod
    def write_to_const(node: Node, var: str):
        raise Error(f"Trying to write into a constant [{var}]", node.get_pos())

    @staticmethod
    def custom(pos: Position, message: str):
        raise Error(message, pos)


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

    @staticmethod
    def label_not_found(name: str):
        raise InternalError(f"Label not found [{name}]")
