from enum import Enum
import re

from .error import lex_error
from .util import Position, sanitize

class TokenType(Enum):
    """
    token types
    """

    NONE      = 0
    ID        = 2
    STRING    = 3
    NUMBER    = 4
    LPAREN    = 5
    RPAREN    = 6
    LBRACE    = 7
    RBRACE    = 8
    LBRACK    = 9
    RBRACK    = 10
    COMMA     = 11
    SEMICOLON = 12
    OPERATOR  = 13
    SET       = 14
    LOGIC     = 15

class Token:
    """
    token of code
    """

    def __init__(self, type_: TokenType, value: str, pos: Position):
        self.type = type_
        self.value = value
        self.pos = pos
    
    def __repr__(self) -> str:
        return f"Token({self.type}, \"{sanitize(self.value)}\", {repr(self.pos)})"

class Lexer:
    """
    splits code into tokens
    """

    # token regexes
    REGEXES = {
        TokenType.ID: re.compile(r"^[a-zA-Z_@][a-zA-Z_0-9]*(\.)?([a-zA-Z_@][a-zA-Z_0-9]*)?$"),
        TokenType.STRING: re.compile("^\"([^\"\\\\]|\\\\.)*\"$"),
        TokenType.NUMBER: re.compile(r"^[0-9]+(\.)?([0-9]+)?$"),
        TokenType.LPAREN: re.compile(r"^\($"),
        TokenType.RPAREN: re.compile(r"^\)$"),
        TokenType.LBRACE: re.compile(r"^\{$"),
        TokenType.RBRACE: re.compile(r"^\}$"),
        TokenType.LBRACK: re.compile(r"^\[$"),
        TokenType.RBRACK: re.compile(r"^\]$"),
        TokenType.COMMA: re.compile(r"^,$"),
        TokenType.SEMICOLON: re.compile(r"^;$"),
        TokenType.OPERATOR: re.compile(r"^[+\-*/!]|(\*\*)|(===)|(<=)|(>=)|(==)|(\!=)|<|>$"),
        TokenType.SET: re.compile(r"^=|(\+=)|(\-=)|(\*=)|(\/=)$"),
        TokenType.LOGIC: re.compile(r"^(\&\&)|(\|\|)$")
    }

    @staticmethod
    def lex(code: str) -> list:
        """
        split code into tokens
        """

        toks = []
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
                    lex_error("Invalid token", ln, Position(lni, start, i, ln))

                # add token to list
                toks.append(Token(Lexer.match(tok), tok, Position(lni, start, i, ln)))
                tok = ""
            
            # add last token
            tok = ln[i:].strip()
            if tok:
                if Lexer.match(tok) != TokenType.NONE:
                    toks.append(Token(Lexer.match(tok), tok, Position(lni, i - len(tok), i, ln)))
                else:
                    lex_error("Invalid token", ln, Position(lni, i - len(tok), i, ln))
        
        return toks

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
