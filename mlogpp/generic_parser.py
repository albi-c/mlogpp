from .tokens import Token, TokenType
from .error import Error


class GenericParser:
    """
        Parses tokens into an AST.
        """

    tokens: list[Token]
    pos: int

    function_stack: list[str]

    loop_stack: list[str]
    loop_count: int

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

        self._init()

        return self.parse_CodeBlock(None, False)

    def _init(self):
        pass

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
