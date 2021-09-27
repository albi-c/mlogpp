from enum import Enum
import re, sys, os

from . import arrows
from .formatting import Format

class TokenType(Enum):
    NONE      = 0
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
    TokenType.ID: re.compile(r"^[a-zA-Z_@][a-zA-Z_0-9]*$"),
    TokenType.STRING: re.compile("^\"([^\"\\\\]|\\\\.)*\"$"),
    TokenType.NUMBER: re.compile(r"^[0-9]+(\.[0-9]+)?$"),
    TokenType.LPAREN: re.compile(r"^\($"),
    TokenType.RPAREN: re.compile(r"^\)$"),
    TokenType.LBRACE: re.compile(r"^\{$"),
    TokenType.RBRACE: re.compile(r"^\}$"),
    TokenType.COMMA: re.compile(r"^,$"),
    TokenType.SEMICOLON: re.compile(r"^;$"),
    TokenType.OPERATOR: re.compile(r"^[+\-*/!]|(\*\*)|(===)|(<=)|(>=)|(==)|(\!=)|<|>$"),
    TokenType.SET: re.compile(r"^=|(\+=)|(\-=)|(\*=)|(\/=)$"),
    TokenType.LOGIC: re.compile(r"^(\&\&)|(\|\|)$"),
    TokenType.DOT: re.compile(r"^\.$")
}

class Position:
    def __init__(self, line: int, column: int, cline: str, len_: int):
        self.line = line
        self.column = column
        self.cline = cline
        self.len = len_
    
    def __repr__(self) -> str:
        return f"Position({self.line}, {self.column}, \"{Token._sanitize(self.cline)}\" {self.len})"
    
    def __str__(self) -> str:
        return f"Position: [line: {self.line}, column: {self.column}, code line: \"{Token._sanitize(self.cline)}\", length: {self.len}]"
    
    def __eq__(self, other) -> bool:
        return self.line == other.line and self.column == other.column

class Token:
    def __init__(self, type_: TokenType, value: str, line: int, col: int, cline: str):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col
        self.cline = cline
    
    def _sanitize(s: str) -> str:
        return s.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
        
    def sanitize_value(self) -> str:
        return Token._sanitize(self.value)
    
    def sanitize_cline(self) -> str:
        return Token._sanitize(self.cline)
    
    def pos(self) -> Position:
        return Position(self.line, self.col, self.cline, len(self.value))
    
    def __repr__(self) -> str:
        return f"Token({self.type}, \"{self.sanitize_value()}\", {self.line}, {self.col}, \"{self.sanitize_cline()}\")"
    
    def __str__(self) -> str:
        return f"Token: [type: {self.type}, value: \"{self.sanitize_value()}\", line: {self.line}, column: {self.col}, code line: \"{self.sanitize_cline()}\"]"
    
    def __eq__(self, other) -> bool:
        return self.type == other.type and self.value == other.value

class Lexer:
    def resolve_includes(code: str) -> str:
        tmp = ""
        for i, ln in enumerate(code.splitlines()):
            if ln.startswith("%"):
                fn = ln[1:]

                if not os.path.isfile(fn):
                    print(f"{Format.ERROR}Error on line {i + 1}: Cannot import file \"{fn}\"{Format.RESET}\n\nHere:\n{ln}\n{arrows.generate(0, len(ln))}")
                    sys.exit(1)
                
                with open(fn, "r") as f:
                    data = f.read()
                
                tmp += data + "\n"
                continue
            
            tmp += ln + "\n"
        
        return tmp

    def lex(code: str) -> list:
        toks = []
        tok = ""
        in_str = False

        for li, ln in enumerate(code.splitlines()):
            st = ln.strip()

            if not st or st.startswith("#"):
                continue
            
            if st.startswith(">") or st.startswith("<"):
                ln = f".{st}"

            st = ln.strip()
            if st.startswith("."):
                ln = f".\"{st[1:]}\""
            
            prev = ""
            for i, c in enumerate(ln):
                if c == " " and not in_str:
                    if Lexer._match(tok) == TokenType.NONE and tok.strip():
                        print(f"{Format.ERROR}Error on line {li + 1}, column {i + 1}: Invalid token \"{tok}\"{Format.RESET}\n\nHere:\n{ln}\n{arrows.generate(i - len(tok), len(tok))}")
                        sys.exit(1)
                    elif tok.strip():
                        toks.append(Token(Lexer._match(tok), tok, li + 1, i - len(tok), ln))
                        tok = ""
                    
                    continue
                
                if c == "\"" and prev != "\\":
                    in_str = not in_str
                
                matched = Lexer._match(tok)

                tok += c

                matches = Lexer._match(tok)

                if tok == "==" and i < len(ln) - 1:
                    if ln[i + 1] == "=":
                        toks.append(Token(TokenType.OPERATOR, "===", li, i - len(tok), ln))
                        tok = ""
                        continue
                elif c == "." and matched == TokenType.NUMBER and matches == TokenType.NONE:
                    continue

                if ((matched != TokenType.NONE) and (matches == TokenType.NONE)) or ((matched != matches) and matched != TokenType.NONE):
                    if tok in ["+=", "-=", "*=", "/=", ">=", "<=", "==", "**"]:
                        toks.append(Token(Lexer._match(tok), tok, li + 1, i - len(tok), ln))
                        tok = ""
                    else:
                        tok = tok[:-1]
                        toks.append(Token(Lexer._match(tok), tok, li + 1, i - len(tok), ln))
                        tok = c

                prev = c

                if len(toks) >= 2:
                    if toks[-1].value == "=" and toks[-2].value == "===":
                        toks.pop()
            
            if Lexer._match(tok) != TokenType.NONE:
                toks.append(Token(Lexer._match(tok), tok, li + 1, i - len(tok), ln))
                tok = ""
            elif tok.strip():
                print(f"{Format.ERROR}Error on line {li + 1}, column {i + 1}: Invalid token \"{tok}\"{Format.RESET}\n\nHere:\n{ln}\n{arrows.generate(i - len(tok), len(tok))}")
                sys.exit(1)

        return toks

    def _match(token: str) -> TokenType:
        for t, r in LEX_REGEXES.items():
            if r.fullmatch(token):
                return t
        
        return TokenType.NONE
    
    def _matchtp(tokens: list, pos: int, pattern: list, *patterns: list) -> bool:
        for p in patterns:
            if len(p) != len(pattern):
                return False

        if pos + len(pattern) > len(tokens):
            return False
        
        matches = [t.type for t in tokens[pos:pos+len(pattern)]] == pattern

        for p in patterns:
            if [t.type for t in tokens[pos:pos+len(p)]] == p:
                matches = True
        
        return matches
    
    def stringify_tokens(tokens: list) -> str:
        return "\n".join([str(t) for t in tokens])
    
    def preprocess(tokens: list) -> list:
        tmp = tokens.copy()

        consts = {}
        found = True
        while found:
            found = False

            for i, t in enumerate(tmp):
                if t.value == "const" and Lexer._matchtp(tmp, i, [TokenType.ID, TokenType.ID, TokenType.SET, TokenType.NUMBER],
                                                                [TokenType.ID, TokenType.ID, TokenType.SET, TokenType.STRING],
                                                                [TokenType.ID, TokenType.ID, TokenType.SET, TokenType.ID]):
                    
                    consts[tmp[i + 1].value] = tmp[i + 3]

                    for _ in range(4):
                        tmp.pop(i)

                    found = True

                    break
        
        for i, t in enumerate(tmp):
            for k, v in consts.items():
                if t.value == k:
                    tmp[i].type = v.type
                    tmp[i].value = v.value
        
        return tmp
