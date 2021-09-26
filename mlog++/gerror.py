import sys, inspect

from .lexer import Token, Position
from . import arrows
from .formatting import Format
from .parser_ import Node

GEN_ERROR_DEBUG = False

def gen_error(node: Node, msg: str) -> None:
    if GEN_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")

    if node is not None:
        print(f"{Format.ERROR}Generator error on line {node.pos.line}, column {node.pos.column}: {msg}{Format.RESET}\n")
        print(f"Here:\n{Token._sanitize(node.pos.cline)}\n{arrows.generate(node.pos.column, node.pos.len)}")
    else:
        print(f"{Format.ERROR}Generator error: {msg}{Format.RESET}")

    sys.exit(1)
