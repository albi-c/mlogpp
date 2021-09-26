import sys, inspect

from .lexer import Token, Position
from . import arrows
from .formatting import Format

PARSE_ERROR_DEBUG = False
LINK_ERROR_DEBUG  = False

def parse_error(tok: Token, msg: str) -> None:
    if PARSE_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")

    print(f"{Format.ERROR}Parser error on line {tok.line}, column {tok.col}: {msg}{Format.RESET}\n")
    print(f"Here:\n{tok.sanitize_cline()}\n{arrows.generate(tok.col, len(tok.value))}")

    sys.exit(1)

def link_error(pos: Position, msg: str) -> None:
    if LINK_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")
    
    print(f"{Format.ERROR}Linker error on line {pos.line}, column {pos.column}: {msg}{Format.RESET}\n")
    print(f"Here:\n{Token._sanitize(pos.cline)}\n{arrows.generate(pos.column, pos.len)}")

    sys.exit(1)
