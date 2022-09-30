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


def lex_error(msg: str, pos: Position = None) -> None:
    """
    raise lexer error
    """

    raise MlogError(msg, pos)


class ParseErrorType(enum.Enum):
    UNEXPECTED_TOKEN = "Unexpected token"
    UNEXPECTED_EOF = "Unexpected EOF"
    INVALID_TOKEN = "Invalid token"


def parse_error(pos: Position, msg: str | ParseErrorType) -> None:
    """
    raise parser error
    """

    if isinstance(msg, ParseErrorType):
        if msg == ParseErrorType.UNEXPECTED_TOKEN:
            raise MlogError(f"{msg.value} [\"{pos.code_section()}\"]", pos)
        else:
            raise MlogError(msg.value, pos)
    else:
        if msg == "Unexpected token":
            raise MlogError(f"{msg} [\"{pos.code_section()}\"]", pos)
        else:
            raise MlogError(msg, pos)


def link_error(pos: Position, msg: str) -> None:
    """
    raise linker error
    """

    raise MlogError(msg, pos)


class GenErrorType(enum.Enum):
    INCOMPATIBLE_TYPES = "Incompatible types"


def gen_error(pos: Position, msg: str | GenErrorType) -> None:
    """
    raise generator error
    """

    if isinstance(msg, GenErrorType):
        raise MlogError(msg.value, pos)
    else:
        raise MlogError(msg, pos)


def error(msg: str) -> None:
    """
    raise error
    """

    raise MlogError(msg)
