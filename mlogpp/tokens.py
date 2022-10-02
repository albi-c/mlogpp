import enum

from .util import Position, sanitize


class TokenType(enum.Flag):
    """
    Token type.
    """

    NONE = enum.auto()
    ID = enum.auto()
    KEYWORD = enum.auto()
    NATIVE = enum.auto()
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


class Token:
    """
    Token.
    """

    type: TokenType
    value: str
    pos: Position

    # builtin types
    TYPES = (
        "num", "str",
        "Block", "Unit", "Team",
        "BlockType", "UnitType", "ItemType", "LiquidType",
        "Controller"
    )
    BLOCK_STATEMENTS = (
        "if", "while", "for",
        "function"
    )
    STATEMENTS = BLOCK_STATEMENTS + (
        "return", "break", "continue",
        "end",
        "else"
    )

    # reserved keywords
    KEYWORDS = TYPES + STATEMENTS

    def __init__(self, type_: TokenType, value: str, pos: Position):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:
        return f"[{self.type}, \"{sanitize(self.value)}\"]"

    def pos(self) -> Position:
        return self.pos
