import sys, inspect

from lexer2 import Token
import arrows
from formatting import Format

PARSE_ERROR_DEBUG = False

def parse_error(tok: Token, msg: str):
    if PARSE_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")

    print(f"{Format.ERROR}Error on line {tok.line}, column {tok.col}: {msg}{Format.RESET}\n\nHere:\n{tok.sanitize_cline()}\n{arrows.generate(tok.col, len(tok.value))}")
    sys.exit(1)
