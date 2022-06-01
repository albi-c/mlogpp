import sys, inspect

from .formatting import Format
from .util import Position

# debug flags
PRE_ERROR_DEBUG = False
LEX_ERROR_DEBUG = False
PARSE_ERROR_DEBUG = False
LINK_ERROR_DEBUG  = False

def pre_error(msg: str, code: str = "", pos: Position = None) -> None:
    """
    raise preprocessor error
    """

    # debug
    if PRE_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")

    if pos is not None:
        print(f"{Format.ERROR}Preprocessor error on line {pos.line}, column {pos.col}: {msg}{Format.RESET}\n")
        print(f"Here:\n{code}\n{arrows.generate(pos.col, pos.len)}")
    else:
        print(f"")

    sys.exit(1)

def lex_error(msg: str, code: str = "", pos: Position = None) -> None:
    """
    raise lexer error
    """

    # debug
    if LEX_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")

    if pos is not None:
        print(f"{Format.ERROR}Lexer error on line {pos.line + 1}, column {pos.start + 1}: {msg}{Format.RESET}\n")
        print(f"Here:\n{code}\n{pos.arrows()}")
    else:
        print(f"{Format.ERROR}Lexer error: {msg}{Format.RESET}\n")

    sys.exit(1)

def parse_error(pos: Position, msg: str) -> None:
    """
    raise parser error
    """

    # debug
    if PARSE_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")

    print(f"{Format.ERROR}Parser error on line {pos.line}, column {pos.start}: {msg}{Format.RESET}\n")
    print(f"Here:\n{pos.code}\n{pos.arrows()}")

    sys.exit(1)

def link_error(pos: Position, msg: str) -> None:
    """
    raise linker error
    """

    # debug
    if LINK_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")
    
    print(f"{Format.ERROR}Linker error on line {pos.line}, column {pos.column}: {msg}{Format.RESET}\n")
    print(f"Here:\n{Token._sanitize(pos.cline)}\n{arrows.generate(pos.column, pos.len)}")

    sys.exit(1)
