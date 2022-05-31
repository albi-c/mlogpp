import sys, inspect

from .lexer import Token, Position
from . import arrows
from .formatting import Format
from .parser_ import Node

GEN_ERROR_DEBUG  = False
GEN_U_ERROR_DEBUG = False
GEN_F_ERROR_DEBUG = False

_undefined_stack = []

def push_undefined(value: bool) -> None:
    _undefined_stack.append(value)

def pop_undefined() -> bool:
    return _undefined_stack.pop()

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

def gen_undefined_error(node: Node, var: str) -> None:
    if len(_undefined_stack) > 0 and not _undefined_stack[-1]:
        return
    
    if GEN_U_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")
    
    if node is not None:
        print(f"{Format.ERROR}Generator error on line {node.pos.line}, column {node.pos.column}: Undefined variable {var}{Format.RESET}\n")
        print(f"Here:\n{Token._sanitize(node.pos.cline)}\n{arrows.generate(node.pos.column, node.pos.len)}")
    else:
        print(f"{Format.ERROR}Generator error: Undefined variable {var}{Format.RESET}")
    
    sys.exit(1)

def gen_undefinedf_error(node: Node, name: str) -> None:
    if GEN_F_ERROR_DEBUG:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(f"In method: {calframe[1][3]}, line: {calframe[1][2]}\n")
    
    if node is not None:
        print(f"{Format.ERROR}Generator error on line {node.pos.line}, column {node.pos.column}: Undefined function {name}{Format.RESET}\n")
        print(f"Here:\n{Token._sanitize(node.pos.cline)}\n{arrows.generate(node.pos.column, node.pos.len)}")
    else:
        print(f"{Format.ERROR}Generator error: Undefined function {name}{Format.RESET}")
    
    sys.exit(1)
