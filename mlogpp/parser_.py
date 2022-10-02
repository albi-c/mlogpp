import genericpath

from .lexer import TokenType, Token
from .error import Error
from .node import *


class Parser:
    """
    Parses tokens into an AST.
    """

    tokens: list[Token]
    pos: int

    function_stack: list[str]

    loop_stack: list[str]
    loop_count: int

    def parse(self, tokens: list[Token]) -> CodeBlockNode:
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

        return self.parse_CodeBlock(None, False)

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

    def parse_Statement(self) -> Node:
        """
        Parse a statement.

        Returns:
            The parsed statement.
        """

        tok = self.next_token()

        match tok.type:
            case TokenType.KEYWORD:
                # variable declaration
                if tok.value in Token.TYPES:
                    name = self.next_token(TokenType.ID)
                    if self.lookahead_token(TokenType.SET, "="):
                        self.next_token(TokenType.SET, "=")
                        value = self.parse_Value()
                        return DeclarationNode(tok.pos + name.pos,
                                               VariableValue(Type.from_code(tok.value), name.value), value)

                    return DeclarationNode(tok.pos + name.pos,
                                           VariableValue(Type.from_code(tok.value), name.value), None)

                # block statement (while, function, ...)
                elif tok.value in Token.BLOCK_STATEMENTS:
                    self.prev_token()
                    return self.parse_BlockStatement()

                match tok.value:
                    # return statement
                    case "return":
                        # check if in a function
                        if len(self.function_stack) > 0:
                            # check if there is a value on the same line
                            if self.lookahead_line() == tok.pos.line:
                                value = self.parse_Value()
                                return ReturnNode(tok.pos + value.get_pos(), self.function_stack[-1], value)

                            return ReturnNode(tok.pos, self.function_stack[-1], None)

                        Error.unexpected_token(tok)

                    # break statement
                    case "break":
                        # check if in a loop
                        if len(self.loop_stack) > 0:
                            return BreakNode(tok.pos, self.loop_stack[-1])

                        Error.unexpected_token(tok)

                    # continue statement
                    case "continue":
                        # check if in a loop
                        if len(self.loop_stack) > 0:
                            return ContinueNode(tok.pos, self.loop_stack[-1])

                        Error.unexpected_token(tok)

                    # end statement
                    case "end":
                        return EndNode(tok.pos)

            case TokenType.ID:
                # assignment
                if self.lookahead_token(TokenType.SET):
                    op = self.next_token(TokenType.SET)
                    value = self.parse_Value()
                    return AssignmentNode(tok.pos + value.get_pos(), tok.value, op.value, value)\

                # function call
                elif self.lookahead_token(TokenType.LPAREN):
                    self.next_token(TokenType.LPAREN)
                    return CallNode(tok.pos, tok.value, self.parse_funcArgVals())

                # indexed memory cell assignment
                elif self.lookahead_token(TokenType.LBRACK):
                    self.next_token(TokenType.LBRACK)
                    index = self.parse_Value()
                    self.next_token(TokenType.RBRACK)

                    op = self.next_token(TokenType.SET)

                    value = self.parse_Value()

                    return IndexedAssignmentNode(tok.pos + value.get_pos(), tok.value, index, op.value, value)

            # native call
            case TokenType.NATIVE:
                self.prev_token()
                return self.parse_NativeCall()

        Error.unexpected_token(tok)

    def parse_NativeCall(self) -> NativeCallNode:
        """
        Parse a native call.

        Returns:
            The parsed native call.
        """

        name = self.next_token(TokenType.NATIVE)
        self.next_token(TokenType.LPAREN)

        # check if the function is native
        if (nat := NativeCallNode.NATIVES.get(name.value)) is not None:
            # how much to subtract when checking if at the end of the function call
            length_check_sub = 1 + (name.value in NativeCallNode.NATIVES_RETURN_POS)

            params = []
            for i in range(len(nat)):
                match nat[i][0]:
                    case Param.UNUSED:
                        params.append("_")
                        continue

                    case Param.INPUT:
                        params.append(self.parse_Value())

                    case Param.CONFIG:
                        params.append(self.next_token(TokenType.ID).value)

                    case Param.OUTPUT:
                        if NativeCallNode.NATIVES_RETURN_POS.get(name.value) == i:
                            params.append("_")
                            continue

                        else:
                            params.append(self.next_token(TokenType.ID).value)

                if i < len(nat) - length_check_sub:
                    self.next_token(TokenType.COMMA)
                else:
                    self.next_token(TokenType.RPAREN)

            return NativeCallNode(name.pos, name.value, params)

        # check if the function is builtin
        elif (nat := NativeCallNode.BUILTINS.get(name.value)) is not None:
            params = []
            for i in range(nat):
                params.append(self.parse_Value())

                if i < nat - 1:
                    self.next_token(TokenType.COMMA)
                else:
                    self.next_token(TokenType.RPAREN)

            return NativeCallNode(name.pos, name.value, params)

        Error.unexpected_token(name)

    def parse_BlockStatement(self) -> IfNode | LoopNode | FunctionNode:
        """
        Parse a block statement.

        Returns:
            The parsed block statement.
        """

        tok = self.next_token(TokenType.KEYWORD)
        if tok.value != "function":
            self.next_token(TokenType.LPAREN)

        match tok.value:
            case "if":
                cond = self.parse_Value()
                self.next_token(TokenType.RPAREN)

                self.next_token(TokenType.LBRACE)
                code = self.parse_CodeBlock(Gen.scope_name())

                if self.lookahead_token(TokenType.KEYWORD, "else"):
                    self.next_token(TokenType.KEYWORD)
                    self.next_token(TokenType.LBRACE)

                    return IfNode(tok.pos, cond, code, self.parse_CodeBlock(Gen.scope_name()))

                return IfNode(tok.pos, cond, code, None)

            case "while":
                cond = self.parse_Value()
                self.next_token(TokenType.RPAREN)

                self.next_token(TokenType.LBRACE)

                name = self.loop_name()

                self.loop_stack.append(name)
                code = self.parse_CodeBlock(name)
                self.loop_stack.pop(-1)

                return WhileNode(tok.pos, name, cond, code)

            case "for":
                # check for range loop
                if self.lookahead_token(TokenType.ID) and self.lookahead_token(TokenType.COLON, None, 2):
                    var = self.next_token(TokenType.ID)
                    self.next_token(TokenType.COLON)
                    until = self.parse_Value()
                    self.next_token(TokenType.RPAREN)

                    self.next_token(TokenType.LBRACE)

                    name = self.loop_name()

                    self.loop_stack.append(name)
                    code = self.parse_CodeBlock(name)
                    self.loop_stack.pop(-1)

                    return RangeNode(tok.pos, name, var.value, until, code)

                init = self.parse_Statement()
                self.next_token(TokenType.SEMICOLON)
                cond = self.parse_Value()
                self.next_token(TokenType.SEMICOLON)
                action = self.parse_Statement()
                self.next_token(TokenType.RPAREN)

                self.next_token(TokenType.LBRACE)

                name = self.loop_name()

                self.loop_stack.append(name)
                code = self.parse_CodeBlock(name)
                self.loop_stack.pop(-1)

                return ForNode(tok.pos, name, init, cond, action, code)

            case "function":
                name = self.next_token(TokenType.ID)
                self.next_token(TokenType.LPAREN)
                params = self.parse_funcArgVars()

                type_ = Type.NULL
                # check for return type
                if self.lookahead_token(TokenType.ARROW):
                    self.next_token(TokenType.ARROW)
                    type_tok = self.next_token(TokenType.KEYWORD)
                    if type_tok.value in Token.TYPES:
                        type_ = Type.from_code(type_tok.value)
                    else:
                        Error.unexpected_token(self.current_token())

                self.next_token(TokenType.LBRACE)
                self.function_stack.append(name.value)
                code = self.parse_CodeBlock(name.value)
                self.function_stack.pop(-1)

                return FunctionNode(tok.pos, name.value, params, type_, code)

    def parse_CodeBlock(self, name: str | None, end_at_rbrace: bool = True):
        """
        Parse a block of code.

        Args:
            name: Name of the code block.
            end_at_rbrace: Break at a right bracket.

        Returns:
            The parsed block of code.
        """

        code = []
        while self.has_token():
            if self.lookahead_token(TokenType.RBRACE) and end_at_rbrace:
                self.next_token()
                break

            code.append(self.parse_Statement())

        return CodeBlockNode(code, name)

    def parse_funcArgVars(self) -> list[tuple[str, Type]]:
        """
        Parse function argument variables.

        Returns:
            The parsed variables.
        """

        variables = []

        last_tok = TokenType.LPAREN
        type_ = None
        while self.has_token():
            tok = self.next_token()

            match tok.type:
                case TokenType.RPAREN:
                    if last_tok in TokenType.COMMA | TokenType.KEYWORD:
                        Error.unexpected_token(tok)

                    break

                case TokenType.COMMA:
                    if last_tok != TokenType.ID:
                        Error.unexpected_token(tok)

                case TokenType.KEYWORD:
                    if last_tok in TokenType.ID | TokenType.KEYWORD or tok.value not in Token.TYPES:
                        Error.unexpected_token(tok)
                    type_ = Type.from_code(tok.value)

                case TokenType.ID:
                    if last_tok != TokenType.KEYWORD:
                        Error.unexpected_token(tok)

                    variables.append((tok.value, type_))

                case _:
                    Error.unexpected_token(tok)

            last_tok = tok.type

        return variables

    def parse_funcArgVals(self) -> list[Node]:
        """
        Parse function argument values.

        Returns:
            The parsed values.
        """

        values = []

        last_tok = TokenType.LPAREN
        while self.has_token():
            tok = self.next_token()

            match tok.type:
                case TokenType.RPAREN:
                    if last_tok == TokenType.COMMA:
                        Error.unexpected_token(tok)

                    break

                case TokenType.COMMA:
                    if last_tok != TokenType.ID:
                        Error.unexpected_token(tok)

                    last_tok = TokenType.COMMA

                case _:
                    if last_tok == TokenType.ID:
                        Error.unexpected_token(tok)

                    last_tok = TokenType.ID
                    self.prev_token()

                    values.append(self.parse_Value())

        return values

    def parse_binaryOp(self, operators: tuple, value_get: callable) -> BinaryOpNode:
        """
        Parse a binary operator.

        Args:
            operators: The possible operators.
            value_get: The function to call to parse a value.

        Returns:
            The parsed binary operator.
        """

        left = value_get()

        right = []
        while self.has_token():
            if self.lookahead_token(TokenType.OPERATOR, operators):
                tok = self.next_token()
                right.append((tok.value, value_get()))

            else:
                break

        pos = left.pos
        if len(right) > 0:
            pos += right[-1][1].pos

        return BinaryOpNode(left.pos, left, right)

    def parse_unaryOp(self, operators: tuple, value_get: callable) -> UnaryOpNode:
        """
        Parse a unary operator.

        Args:
            operators: The possible operators.
            value_get: The function to call to parse a value.

        Returns:
            The parsed unary operator.
        """

        operations = []
        while self.has_token():
            if self.lookahead_token(TokenType.OPERATOR, operators):
                tok = self.next_token()
                if tok.value in operations:
                    operations.remove(tok.value)
                else:
                    operations.append(tok.value)

            else:
                break

        value = value_get()
        for op in operations:
            value = UnaryOpNode(value.get_pos(), op, value)

        return value

    def parse_Value(self) -> BinaryOpNode:
        """
        Parse a value.

        Returns:
            The parsed value.
        """

        return self.parse_OrTest()

    def parse_OrTest(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("||",),
            self.parse_AndTest
        )

    def parse_AndTest(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("&&",),
            self.parse_NotTest
        )

    def parse_NotTest(self) -> UnaryOpNode:
        return self.parse_unaryOp(
            ("!",),
            self.parse_Comparison
        )

    def parse_Comparison(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("<", ">", "==", "===", ">=", "!="),
            self.parse_OrExpr
        )

    def parse_OrExpr(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("|",),
            self.parse_XorExpr
        )

    def parse_XorExpr(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("^",),
            self.parse_AndExpr
        )

    def parse_AndExpr(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("&",),
            self.parse_ShiftExpr
        )

    def parse_ShiftExpr(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("<<", ">>"),
            self.parse_ArithExpr
        )

    def parse_ArithExpr(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("+", "-"),
            self.parse_Term
        )

    def parse_Term(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("*", "/", "//", "%"),
            self.parse_Factor
        )

    def parse_Factor(self) -> UnaryOpNode:
        return self.parse_unaryOp(
            ("-", "~"),
            self.parse_Power
        )

    def parse_Power(self) -> BinaryOpNode:
        return self.parse_binaryOp(
            ("**",),
            self.parse_Call
        )

    def parse_Call(self) -> CallNode | NativeCallNode | ValueNode | BinaryOpNode:
        """
        Parse a function call or operator.

        Returns:
            The function call or operator.
        """

        # check if a function call
        if self.lookahead_token(TokenType.ID) and self.lookahead_token(TokenType.LPAREN, None, 2):
            name = self.next_token(TokenType.ID)
            self.next_token(TokenType.LPAREN)
            params = self.parse_funcArgVals()
            return CallNode(name.pos, name.value, params)

        # check if a native function call
        elif self.lookahead_token(TokenType.NATIVE):
            return self.parse_NativeCall()

        return self.parse_Atom()

    def parse_Atom(self) -> ValueNode | BinaryOpNode:
        """
        Parse a value or an operator.

        Returns:
            The value or operator.
        """

        tok = self.next_token()

        match tok.type:
            case TokenType.ID:
                if self.lookahead_token(TokenType.LBRACK):
                    self.next_token(TokenType.LBRACK)
                    index = self.parse_Value()
                    self.next_token(TokenType.RBRACK)

                    # declare the value if it is a linked block
                    for block in constants.BLOCK_LINKS:
                        if tok.value.startswith(block) and len(tok.value) > len(block):
                            try:
                                int(tok.value[len(block):])
                            except ValueError:
                                pass
                            else:
                                Scopes.add(VariableValue(Type.BLOCK, tok.value, True))

                    return IndexedValueNode(tok.pos + index.pos, tok.value, index)

                # check if the value is a content
                elif len(tok.value) > 1 and tok.value.startswith("@"):
                    if tok.value[1:] in constants.BLOCKS:
                        return ContentValueNode(tok.pos, tok.value, Type.BLOCK_TYPE)
                    elif tok.value[1:] in constants.ITEMS:
                        return ContentValueNode(tok.pos, tok.value, Type.ITEM_TYPE)
                    elif tok.value[1:] in constants.LIQUIDS:
                        return ContentValueNode(tok.pos, tok.value, Type.LIQUID_TYPE)
                    elif tok.value[1:] in constants.UNITS:
                        return ContentValueNode(tok.pos, tok.value, Type.UNIT_TYPE)
                    elif tok.value[1:] in constants.TEAMS:
                        return ContentValueNode(tok.pos, tok.value, Type.TEAM)

                # check if the value is a property access
                if "." in tok.value:
                    spl = tok.value.split(".")

                    # declare the value if it is a linked block
                    for block in constants.BLOCK_LINKS:
                        if spl[0].startswith(block) and len(spl[0]) > len(block):
                            try:
                                int(spl[0][len(block):])
                            except ValueError:
                                pass
                            else:
                                Scopes.add(VariableValue(Type.BLOCK, spl[0], True))

                # declare the value if it is a linked block
                for block in constants.BLOCK_LINKS:
                    if tok.value.startswith(block) and len(tok.value) > len(block):
                        try:
                            int(tok.value[len(block):])
                        except ValueError:
                            pass
                        else:
                            Scopes.add(VariableValue(Type.BLOCK, tok.value, True))

                return VariableValueNode(tok.pos, tok.value)

            case TokenType.STRING:
                return StringValueNode(tok.pos, tok.value)

            case TokenType.NUMBER:
                try:
                    val = float(tok.value)
                except ValueError:
                    Error.unexpected_token(tok)
                else:
                    # convert the value to an integer if whole
                    if val.is_integer():
                        val = int(val)

                    return NumberValueNode(tok.pos, val)

            case TokenType.LPAREN:
                value = self.parse_Value()
                self.next_token(TokenType.RPAREN)

                return value

        Error.unexpected_token(tok)
