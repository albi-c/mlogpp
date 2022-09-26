import enum
import re

from .error import lex_error
from .util import Position, sanitize


class TokenType(enum.Enum):
    """
    token types
    """

    NONE = enum.auto()
    ID = enum.auto()
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
    OPERATOR = enum.auto()
    SET = enum.auto()
    LOGIC = enum.auto()


class Token:
    """
    token of code
    """

    type: TokenType
    value: str
    pos: Position

    def __init__(self, type_: TokenType, value: str, pos: Position):
        self.type = type_
        self.value = value
        self.pos = pos
    
    def __repr__(self) -> str:
        return f"[{self.type}, \"{sanitize(self.value)}\"]"
    
    def pos(self) -> Position:
        return self.pos


class Lexer:
    """
    splits code into tokens
    """

    # token regexes
    REGEXES = {
        TokenType.ID: re.compile(r"^[a-zA-Z_@][a-zA-Z_0-9\-]*(\.)?([a-zA-Z_@][a-zA-Z_0-9\-]*)?$"),
        TokenType.STRING: re.compile("^\"([^\"\\\\]|\\\\.)*\"$"),
        TokenType.NUMBER: re.compile(r"^[0-9]+(\.)?([0-9]+)?$"),
        TokenType.LPAREN: re.compile(r"^\($"),
        TokenType.RPAREN: re.compile(r"^\)$"),
        TokenType.LBRACE: re.compile(r"^\{$"),
        TokenType.RBRACE: re.compile(r"^}$"),
        TokenType.LBRACK: re.compile(r"^\[$"),
        TokenType.RBRACK: re.compile(r"^]$"),
        TokenType.COMMA: re.compile(r"^,$"),
        TokenType.SEMICOLON: re.compile(r"^;$"),
        TokenType.COLON: re.compile(r"^:$"),
        TokenType.OPERATOR: re.compile(r"^[+\-*/!]|(\*\*)|(===)|(<=)|(>=)|(==)|(!=)|<|>|~$"),
        TokenType.SET: re.compile(r"^=|(\+=)|(-=)|(\*=)|(/=)$"),
        TokenType.LOGIC: re.compile(r"^(&&)|(\|\|)$")
    }

    JOINABLE_TOKENS = {
        TokenType.ID, TokenType.NUMBER
    }

    @staticmethod
    def lex(code: str) -> list:
        """
        split code into tokens
        """

        tokens = []
        # iterate over lines
        for lni, ln in enumerate(code.splitlines()):
            ln = ln.strip()

            # skip if empty or comment
            if not ln or ln.startswith("#"):
                continue
            
            tok = ""
            i = 0
            while True:
                start = i

                # continue if character is whitespace
                if not ln[i].strip():
                    i += 1
                    continue
                
                # add characters until it matches
                while Lexer.match(tok) == TokenType.NONE:
                    if i >= len(ln):
                        break

                    c = ln[i]
                    tok += c
                    i += 1
                
                # add characters until it doesn't match anymore
                while Lexer.match(tok) != TokenType.NONE:
                    if i >= len(ln):
                        break

                    c = ln[i]
                    tok += c
                    i += 1

                # go one character back
                i -= 1
                tok = tok[:-1]

                # break if token is empty
                if not tok.strip():
                    break
                
                # error if invalid token
                if Lexer.match(tok) == TokenType.NONE:
                    lex_error(f"Invalid token: [\"{tok}\"]", Position(lni, start, i, ln))

                # add token to list
                tokens.append(Token(Lexer.match(tok), tok, Position(lni, start, i, ln)))
                tok = ""
            
            # add last token
            tok = ln[i:].strip()
            if tok:
                token_type = Lexer.match(tok)
                if token_type != TokenType.NONE:
                    if len(tokens) > 0 and token_type == tokens[-1].type and lni == tokens[-1].pos.line and token_type in Lexer.JOINABLE_TOKENS:
                        tokens[-1].pos.end += len(tok)
                        tokens[-1].value += tok
                    else:
                        tokens.append(Token(Lexer.match(tok), tok, Position(lni, i - len(tok), i, ln)))
                else:
                    lex_error("Invalid token", Position(lni, i - len(tok), i, ln))
        
        return tokens

    @staticmethod
    def match(token: str) -> TokenType:
        """
        match a token to a type
        """
        
        # iterate over regexes
        for t, r in Lexer.REGEXES.items():
            if r.fullmatch(token):
                return t
        
        return TokenType.NONE
