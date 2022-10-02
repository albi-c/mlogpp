import os
import string

from .preprocess import Preprocessor
from .error import Error
from .util import Position, sanitize
from .node import NativeCallNode
from .tokens import *


class Lexer:
    """
    Splits code into tokens.
    """

    # identifier characters
    ID_CHARS_START = string.ascii_letters + "_@"
    ID_CHARS = ID_CHARS_START + "-." + string.digits

    STRING_CHARS = string.printable

    NUMBER_CHARS_START = string.digits
    NUMBER_CHARS = NUMBER_CHARS_START + "."

    OPERATOR_CHARS_START = "+-*/%=<>!&|^~"

    SET_CHARS_START = "=+-*/%&|^<>"

    include_search_dir: str
    imported_files: set

    current_input_file: str
    current_code: str
    current_code_lines: list[str]
    i: int
    line: int
    char: int

    def __init__(self, include_search_dir: str):
        self.include_search_dir = include_search_dir
        self.imported_files = set()

        self.current_input_file = ""
        self.current_code = ""
        self.current_code_lines = []
        self.i = -1
        self.line = 0
        self.char = 0

    def next_char(self, char: str | None = None) -> str:
        """
        Read the next character.

        Args:
            char: The expected character. Null for any character.

        Returns:
            The read character.
        """

        # increase the character pointer
        self.i += 1

        # if there is no more characters, return ""
        if self.i >= len(self.current_code):
            return ""

        # read the next character
        ch = self.current_code[self.i]
        # if the character doesn't match with the expected one, error
        if char is not None and ch != char:
            Error.unexpected_character(self.make_position(1), ch)

        # increase the line and column counters
        self.char += 1
        if ch == "\n":
            self.char = 0
            self.line += 1

        return ch

    def lookahead_char(self, char: str | None = None) -> str | bool:
        """
        Look at the next character.

        Args:
            char: The expected character. None for any character.

        Returns:
            The next character matching with the expected one if it is not None.
            Else the next character.
        """

        # check if there is a character available
        if self.i + 1 >= len(self.current_code):
            return ""

        # check if the next character matches
        if self.current_code[self.i + 1] == char:
            self.next_char()
            return True

        # the next character doesn't match
        elif char is not None:
            return False

        # char == None, return the next character
        return self.current_code[self.i + 1]

    def prev_char(self):
        """
        Step one character back.
        """

        # check if stepping back is possible
        if self.i > -1:
            # decrease the character pointer
            self.i -= 1
            # decrease the column counter
            self.char -= 1
            # step back to the previous line
            if self.char < 0:
                self.char = len(self.current_code_lines[self.line - 1])
                self.line -= 1

    def make_position(self, length: int) -> Position:
        """
        Create a position from the current line and column counters.

        Args:
            length: Length of the position.

        Returns:
            The created position.
        """

        return Position(self.line, self.char - length, self.char, self.current_code_lines[self.line],
                        self.current_input_file)

    def make_token(self, type_: TokenType, value: str) -> Token:
        """
        Create a token.

        Args:
            type_: Type of the token.
            value: Value of the token.

        Returns:
            The created token.
        """

        return Token(type_, value, self.make_position(len(value)))

    def lex(self, code: str, input_file: str) -> list[Token]:
        """
        Split code into tokens.

        Args:
            code: Input code.
            input_file: File of the input code, used for imports and errors.

        Returns:
            A list of tokens from the code.
        """

        # save variables, used for import recursion
        old_current_code = self.current_code
        self.current_code = code
        old_current_code_lines = self.current_code_lines
        self.current_code_lines = code.splitlines()
        old_current_input_file = self.current_input_file
        self.current_input_file = input_file
        old_i = self.i
        self.i = -1
        old_line = self.line
        self.line = 0
        old_char = self.char
        self.char = 0

        # list of lexed tokens
        tokens = []
        while ch := self.lookahead_char():
            # break at the end of code
            if ch == "":
                break

            # skip whitespaces
            if not ch.strip():
                self.next_char()
                continue

            # skip comments
            if ch == "#":
                self.lex_until_eol()
                continue

            # imports
            if ch == "%" and self.char == 0:
                # read until the end of line
                token = self.lex_until_eol()

                # if token is not only "%"
                if len(token) > 1:
                    path = os.path.join(self.include_search_dir, token[1:])
                    # check if imported file exists
                    if os.path.isfile(path):
                        # check if file is already imported
                        if path in self.imported_files:
                            Error.already_imported(self.make_position(len(token)), path)

                        # add the file to list of imported files
                        self.imported_files.add(path)

                        with open(path, "r") as f:
                            imported_code = f.read()

                        # preprocess the imported file
                        imported_code = Preprocessor.preprocess(imported_code)
                        # add tokens of the imported file to the currently parsed ones
                        tokens += self.lex(imported_code, path)

                    else:
                        Error.cannot_find_file(self.make_position(len(token)), path)

            # lex an identifier
            elif ch in self.ID_CHARS_START and (token := self.lex_id()) is not None:
                # check if the identifier is a keyword
                if token in Token.KEYWORDS:
                    tokens.append(self.make_token(TokenType.KEYWORD, token))

                # check if the identifier is a native or builtin function
                elif token in NativeCallNode.NATIVES or token in NativeCallNode.BUILTINS:
                    tokens.append(self.make_token(TokenType.NATIVE, token))

                else:
                    tokens.append(self.make_token(TokenType.ID, token))

            # lex a string
            elif ch == '"' and (token := self.lex_string()) is not None:
                tokens.append(self.make_token(TokenType.STRING, token))

            # lex a number
            elif ch in self.NUMBER_CHARS_START and (token := self.lex_number()) is not None:
                tokens.append(self.make_token(TokenType.NUMBER, token))

            # lex one character tokens

            elif ch == "(":
                self.next_char()
                tokens.append(self.make_token(TokenType.LPAREN, ch))
            elif ch == ")":
                self.next_char()
                tokens.append(self.make_token(TokenType.RPAREN, ch))

            elif ch == "{":
                self.next_char()
                tokens.append(self.make_token(TokenType.LBRACE, ch))
            elif ch == "}":
                self.next_char()
                tokens.append(self.make_token(TokenType.RBRACE, ch))

            elif ch == "[":
                self.next_char()
                tokens.append(self.make_token(TokenType.LBRACK, ch))
            elif ch == "]":
                self.next_char()
                tokens.append(self.make_token(TokenType.RBRACK, ch))

            elif ch == ",":
                self.next_char()
                tokens.append(self.make_token(TokenType.COMMA, ch))
            elif ch == ";":
                self.next_char()
                tokens.append(self.make_token(TokenType.SEMICOLON, ch))
            elif ch == ":":
                self.next_char()
                tokens.append(self.make_token(TokenType.COLON, ch))

            # lex an arrow
            elif ch == "-" and (token := self.lex_arrow()) is not None:
                tokens.append(self.make_token(TokenType.ARROW, token))

            # lex assignment operators
            elif ch in Lexer.SET_CHARS_START and (token := self.lex_set()) is not None:
                tokens.append(self.make_token(TokenType.SET, token))

            # lex operators
            elif ch in Lexer.OPERATOR_CHARS_START and (token := self.lex_operator()) is not None:
                tokens.append(self.make_token(TokenType.OPERATOR, token))

            else:
                Error.unexpected_character(self.make_position(1), ch)

        # restore variables
        self.current_code = old_current_code
        self.current_code_lines = old_current_code_lines
        self.current_input_file = old_current_input_file
        self.i = old_i
        self.line = old_line
        self.char = old_char

        return tokens

    def lex_until_eol(self) -> str:
        """
        Lex until the end of line.

        Returns:
            The lexed line.
        """

        token = ""
        while (ch := self.next_char()) != "\n":
            token += ch

        return token

    def lex_id(self) -> str:
        """
        Lex an identifier.

        Returns:
            The lexed token.
        """

        token = ""
        while (ch := self.lookahead_char()) in Lexer.ID_CHARS:
            self.next_char()

            if ch == ".":
                # check if "." is already used
                if "." in token:
                    Error.unexpected_character(self.make_position(1), ch)

                else:
                    token += ch

                    # check if "." is at the end of the token
                    if (ch := self.lookahead_char()) not in Lexer.ID_CHARS:
                        Error.unexpected_character(self.make_position(1), ch)

                    continue

            token += ch

        return token

    def lex_string(self) -> str:
        """
        Lex a string.

        Returns:
            The lexed token.
        """

        # skip the first quote
        self.next_char()

        token = ""
        while (ch := self.next_char()) in Lexer.STRING_CHARS:
            # end the string when encountering a second quote
            if ch == '"':
                return f"\"{token}\""

            token += ch

        return f"\"{token}\""

    def lex_number(self) -> str:
        """
        Lex a number.

        Returns:
            The lexed token.
        """

        token = ""
        while (ch := self.lookahead_char()) in Lexer.NUMBER_CHARS:
            self.next_char()

            # check if "." is already used
            if ch == "." and "." in token:
                Error.unexpected_character(self.make_position(1), ch)

            token += ch

        return token

    def lex_arrow(self) -> str | None:
        """
        Lex an arrow.

        Returns:
            The lexed token.
        """

        if self.next_char() == "-":
            if self.next_char() == ">":
                return "->"

            self.prev_char()

        self.prev_char()

    def lex_operator(self) -> str | None:
        """
        Lex an operator.

        Returns:
            The lexed token.
        """

        match ch := self.next_char():
            # + - ~ ^ %
            case "+" | "-" | "~" | "^" | "%":
                return ch
            # & && | ||
            case "&" | "|":
                if self.lookahead_char(ch):
                    return ch + ch
                return ch
            # * **
            case "*":
                if self.lookahead_char("*"):
                    return "**"
                return "*"
            # / //
            case "/":
                if self.lookahead_char("/"):
                    return "//"
                return "/"
            # == ===
            case "=":
                if self.lookahead_char("="):
                    if self.lookahead_char("="):
                        return "==="
                    return "=="
            # < <= > >=
            case "<" | ">":
                if self.lookahead_char("="):
                    return ch + "="
                elif self.lookahead_char(ch):
                    return ch + ch
                return ch
            # ! !=
            case "!":
                if self.lookahead_char("="):
                    return "!="
                return "!"

        # step back if nothing matched
        self.prev_char()

    def lex_set(self) -> str | None:
        """
        Lex an assignment operator.

        Returns:
            The lexed token.
        """

        match ch := self.next_char():
            # =
            case "=":
                if self.lookahead_char() == "=":
                    self.prev_char()
                    return None
                return ch
            # += -= %= &= |= ^=
            case "+" | "-" | "%" | "&" | "|" | "^":
                if self.lookahead_char("="):
                    return ch + "="
            # *= **= /= //=
            case "*" | "/":
                if self.lookahead_char() == ch:
                    self.next_char()
                    if self.lookahead_char("="):
                        return ch + ch + "="
                    self.prev_char()
                elif self.lookahead_char("="):
                    return ch + "="
            # <<= >>=
            case "<" | ">":
                if self.lookahead_char(ch):
                    if self.lookahead_char("="):
                        return ch + ch + "="
                    self.prev_char()

        # step back if nothing matched
        self.prev_char()
