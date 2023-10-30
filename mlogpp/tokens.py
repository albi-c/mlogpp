import enum

from .util import Position, sanitize


class TokenType(enum.Flag):
    """
    Token type.
    """

    NONE = enum.auto()
    ID = enum.auto()
    KEYWORD = enum.auto()
    STRING = enum.auto()
    NUMBER = enum.auto()
    LPAREN = enum.auto()
    RPAREN = enum.auto()
    LBRACE = enum.auto()
    RBRACE = enum.auto()
    LBRACK = enum.auto()
    RBRACK = enum.auto()
    COMMA = enum.auto()
    SEMICOLON = enum.auto()
    COLON = enum.auto()
    ARROW = enum.auto()
    OPERATOR = enum.auto()
    SET = enum.auto()
    DOLLAR = enum.auto()


class Token:
    """
    Token.
    """

    type: TokenType
    value: str
    pos: Position

    BLOCK_STATEMENTS = (
        "if", "elif", "else",
        "while", "for",
        "function",
        "struct",
        "asm"
    )
    STATEMENTS = BLOCK_STATEMENTS + (
        "return",
        "break", "continue",
        "configuration", "const"
    )

    # reserved keywords
    KEYWORDS = STATEMENTS

    def __init__(self, type_: TokenType, value: str, pos: Position):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:
        return f"[{self.type}, \"{sanitize(self.value)}\"]"

    def pos(self) -> Position:
        return self.pos
