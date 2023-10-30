from abc import ABC, abstractmethod

from .tokens import Token, TokenType
from .error import Error
from .expression import Expression
from .util import Position
from .lexer import Lexer


class GenericParser(ABC):
    """
    Parses tokens into an AST.
    """

    tokens: list[Token]
    pos: int

    function_stack: list[str]

    loop_stack: list[str]
    loop_count: int

    const_expressions: bool
    token_preprocess_start: TokenType

    def parse(self, tokens: list[Token]):
        """
        Parse tokens into an AST.

        Args:
            tokens: The tokens to be parsed.

        Returns:
            The parsed AST.
        """

        self.tokens = tokens
        self.pos = -1

        self.function_stack = []

        self.loop_stack = []
        self.loop_count = 0

        self.const_expressions = False
        self.token_preprocess_start = TokenType.LBRACE

        self._init()

        while self._preprocess_tokens():
            pass

        return self.parse_CodeBlock(False)

    @abstractmethod
    def parse_CodeBlock(self, end_at_rbrace: bool):
        raise NotImplementedError

    def _init(self):
        pass

    @staticmethod
    def _lex_const_val(pos: Position, val: str) -> list[Token]:
        pos.start += 2
        pos.end += 2
        tokens = Lexer("").lex(val, pos.file, pos)
        for tok in tokens:
            tok.pos.code = pos.code
        return tokens

    @staticmethod
    def _val_into_tokens(pos: Position, val, nested: bool = False) -> tuple[list[Token], int]:
        if isinstance(val, str):
            if val.startswith("\"") and val.endswith("\""):
                return [Token(TokenType.STRING, val, pos)], 0
            elif not val.startswith("\"") and not val.endswith("\""):
                return GenericParser._lex_const_val(pos, val), 0
            else:
                return Lexer("").lex(val, pos.file, pos), 0

        elif isinstance(val, int | float):
            return [Token(TokenType.NUMBER, str(val), pos)], 0

        elif isinstance(val, bool):
            return [Token(TokenType.NUMBER, str(int(val)), pos)], 0

        elif isinstance(val, list):
            tokens = []
            if nested:
                for v in val:
                    t, r = GenericParser._val_into_tokens(pos, v, True)
                    if r != 0:
                        return [], r
                    tokens += t
                return tokens, 0

            if len(val) > 0:
                return GenericParser._val_into_tokens(pos, val[-1], True)

            else:
                return [], 1

        elif val is None:
            return [], 0

        else:
            return [], -1

    def _preprocess_tokens(self) -> bool:
        if not self.const_expressions:
            return False

        for i, tok in enumerate(self.tokens):
            if tok.type not in self.token_preprocess_start:
                continue

            expr = []

            end = tok
            j = i + (1 if self.token_preprocess_start == TokenType.LBRACE else 2)
            while j < len(self.tokens):
                t = self.tokens[j]
                if t.type == TokenType.RBRACE:
                    end = t
                    break
                elif t.type in Expression.TOKENS:
                    if t.type == TokenType.SET and t.value != "=":
                        Error.unexpected_token(t)

                    expr.append(t.value)
                else:
                    Error.unexpected_token(tok)
                j += 1

            tok.pos += end.pos

            for _ in range(len(expr) + (2 if self.token_preprocess_start == TokenType.LBRACE else 3)):
                self.tokens.pop(i)

            expr = "\n".join(ln.strip() for ln in " ".join(expr).splitlines())

            val = Expression.exec(tok.pos, expr)

            tokens, err = GenericParser._val_into_tokens(tok.pos, val)

            if err == -1 or err == 1:
                Error.custom(tok.pos, f"Invalid const expression [{expr}]")

            self.tokens[i:i] = tokens

            self._init()

            return True

        return False

    def loop_name(self) -> str:
        """
        Generate a unique loop name.

        Returns:
            The generated loop name.
        """

        self.loop_count += 1
        return f"__loop_{self.loop_count}"

    def has_token(self, n: int = 1) -> bool:
        """
        Check if there are available tokens.

        Args:
            n: How many tokens should be available.

        Returns:
            True if `n` tokens are available, otherwise False.
        """

        return self.pos < len(self.tokens) - n

    def current_token(self) -> Token:
        """
        Get the current token.

        Returns:
            The current token.
        """

        return self.tokens[self.pos]

    def prev_token(self, n: int = 1) -> None:
        """
        Step `n` tokens back.

        Args:
            n: How many tokens to step back.
        """

        self.pos -= n

    def next_token(self, type_: TokenType | None = None, value: str | tuple | list | None = None) -> Token:
        """
        Step to the next token.

        Args:
            type_: The expected type of the token.
            value: The expected value(s) of the token.

        Returns:
            The next token.
        """

        # check if there is a token available
        if self.has_token():
            self.pos += 1

            tok = self.current_token()

            # check if the token is of the correct type
            if type_ is not None and tok.type not in type_:
                Error.unexpected_token(tok)

            # check if the token has the correct value
            if value is not None:
                if isinstance(value, str):
                    if tok.value != value:
                        Error.unexpected_token(tok)
                else:
                    if tok.value not in value:
                        Error.unexpected_token(tok)

            return tok

        Error.unexpected_token(self.tokens[self.pos - 1])

    def lookahead_token(self, type_: TokenType, value: str | tuple | list | None = None, n: int = 1) -> bool:
        """
        Check if a forward token matches.

        Args:
            type_: The expected type of the token.
            value: The expected value(s) of the token.
            n: How many tokens to look forward.

        Returns:
            True if the token matches, False otherwise.
        """

        # check if there is `n` tokens available
        if self.has_token(n):
            tok = self.tokens[self.pos + n]

            # check if the token has the correct value
            if value is not None:
                if isinstance(value, str):
                    if tok.value != value:
                        return False
                else:
                    if tok.value not in value:
                        return False

            # check if the token has the correct type
            return tok.type in type_

        return False

    def lookahead_line(self, n: int = 1) -> int:
        """
        Get the line of a forward token.

        Args:
            n: How many tokens to look forward.

        Returns:
            The line of the token, -1 if there is not enough tokens.
        """

        if self.has_token(n):
            return self.tokens[self.pos + n].pos.line

        return -1
