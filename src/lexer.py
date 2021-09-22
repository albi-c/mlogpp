from enum import Enum
import re

class TokenType(Enum):
    NONE      = 0
    SEPARATOR = 1
    ID        = 2
    STRING    = 3
    NUMBER    = 4
    LPAREN    = 5
    RPAREN    = 6
    LBRACE    = 7
    RBRACE    = 8
    COMMA     = 9
    SEMICOLON = 10
    OPERATOR  = 11
    SET       = 12
    LOGIC     = 13
    DOT       = 14

LEX_REGEXES = {
    TokenType.SEPARATOR: re.compile("^\n+$"),
    TokenType.ID: re.compile(r"^[a-zA-Z_@][a-zA-Z_0-9]*$"),
    TokenType.STRING: re.compile("^\"([^\"\\\\]|\\\\.)*\"$"),
    TokenType.NUMBER: re.compile(r"^[0-9]+(\.[0-9]+)?$"),
    TokenType.LPAREN: re.compile(r"^\($"),
    TokenType.RPAREN: re.compile(r"^\)$"),
    TokenType.LBRACE: re.compile(r"^\{$"),
    TokenType.RBRACE: re.compile(r"^\}$"),
    TokenType.COMMA: re.compile(r"^,$"),
    TokenType.SEMICOLON: re.compile(r"^;$"),
    TokenType.OPERATOR: re.compile(r"^[+\-*/]|(\*\*)|(<=)|(>=)|(==)|(\!=)|<|>$"),
    TokenType.SET: re.compile(r"^=|(\+=)|(\-=)|(\*=)|(\/=)$"),
    TokenType.LOGIC: re.compile(r"^(\&\&)|(\|\|)$"),
    TokenType.DOT: re.compile(r"^\.$")
}

class Token:
    def __init__(self, type_: TokenType, value: str):
        self.type = type_
        self.value = value
    
    def sanitize_value(self) -> str:
        return self.value.replace("\n", "\\n")
    
    def __repr__(self) -> str:
        return f"Token({self.type}, \"{self.sanitize_value()}\")"
    
    def __str__(self) -> str:
        return f"Token: [type: {self.type}, value: \"{self.sanitize_value()}\"]"
    
    def __eq__(self, other) -> bool:
        return self.type == other.type and self.value == other.value

class Lexer:
    def lex(self, code: str) -> list:
        toks = []
        tok = ""

        for c in code:
            matched = self.match(tok)

            tok += c

            matches = self.match(tok)

            if tok[:-1] == "function":
                tok = tok[:-1]
                toks.append(Token(self.match(tok), tok))
                tok = c
                continue
            elif tok[:-1] in ["return", "break", "continue"]:
                tok = tok[:-1]
                toks.append(Token(self.match(tok), tok))
                tok = c
                continue
            elif matched == TokenType.NUMBER and matches == TokenType.NONE and c == ".":
                continue

            if ((matched != TokenType.NONE) and (matches == TokenType.NONE)) or ((matched != matches) and matched != TokenType.NONE):
                if tok in ["+=", "-=", "*=", "/=", ">=", "<=", "==", "**"]:
                    toks.append(Token(self.match(tok), tok))
                    tok = ""
                else:
                    tok = tok[:-1]
                    toks.append(Token(self.match(tok), tok))
                    tok = c
        
        if (self.match(tok) != TokenType.NONE):
            toks.append(Token(self.match(tok), tok))
        
        toks = self._strip_toks(toks)

        return toks
    
    def _strip_toks(self, toks: list) -> list:
        first = -1
        last = -1

        for i, t in enumerate(toks):
            if t.type != TokenType.SEPARATOR and first == -1:
                first = i
            
            if t.type == TokenType.SEPARATOR and first != -1:
                last = i

        return toks[first:last]

    def match(self, token: str) -> TokenType:
        for t, r in LEX_REGEXES.items():
            if r.fullmatch(token):
                return t
        
        return TokenType.NONE
