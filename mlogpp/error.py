from .formatting import Format
from .util import Position


class MlogError(Exception):
    def __init__(self, msg: str, pos: Position = None):
        self.message = f"{msg}: {pos}"

        self.msg = msg
        self.pos = pos
    
    def print(self):
        if self.pos is not None:
            print(f"{Format.ERROR}{Format.BOLD}Error{Format.RESET}{Format.ERROR} on line {self.pos.line}, column {self.pos.start}: {self.msg}{Format.RESET}")
            print(f"Here:\n{self.pos.code}\n{self.pos.arrows()}")
        else:
            print(f"{Format.ERROR}{Format.BOLD}Error{Format.RESET}{Format.ERROR}: {self.msg}{Format.RESET}")


def lex_error(msg: str, pos: Position = None) -> None:
    """
    raise lexer error
    """

    raise MlogError(msg, pos)


def parse_error(pos: Position, msg: str) -> None:
    """
    raise parser error
    """

    if msg == "Unexpected token":
        raise MlogError(f"{msg} [\"{pos.code_section()}\"]", pos)
    else:
        raise MlogError(msg, pos)


def link_error(pos: Position, msg: str) -> None:
    """
    raise linker error
    """

    raise MlogError(msg, pos)


def gen_error(pos: Position, msg: str) -> None:
    """
    raise generator error
    """

    raise MlogError(msg, pos)


def error(msg: str) -> None:
    """
    raise error
    """

    raise MlogError(msg)
