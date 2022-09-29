from .lexer import TokenType, Token
from .error import parse_error, ParseErrorType
from .node_rewrite import *
from . import functions


class Parser:
    """
    parses tokens into an AST
    """

    tokens: list[Token]
    pos: int

    function_stack: list[str]

    loop_stack: list[str]
    loop_count: int

    def parse(self, tokens: list[Token]) -> CodeBlockNode:
        self.tokens = tokens
        self.pos = -1

        self.function_stack = []

        self.loop_stack = []
        self.loop_count = 0

        return self.parse_CodeBlock()

    def loop_name(self) -> str:
        self.loop_count += 1
        return f"__loop_{self.loop_count}"

    def has_token(self, n: int = 1) -> bool:
        return self.pos < len(self.tokens) - n

    def current_token(self) -> Token:
        return self.tokens[self.pos]

    def prev_token(self, n: int = 1):
        self.pos -= n

    def next_token(self, type_: TokenType | None = None, value: str | tuple | list | None = None) -> Token:
        if self.has_token():
            self.pos += 1

            tok = self.current_token()

            if type_ is not None and tok.type not in type_:
                parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

            if value is not None:
                if isinstance(value, str):
                    if tok.value != value:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)
                else:
                    if tok.value not in value:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

            return tok

        parse_error(self.tokens[self.pos - 1].pos, ParseErrorType.UNEXPECTED_EOF)

    def lookahead_token(self, type_: TokenType, value: str | tuple | list | None = None, n: int = 1) -> bool:
        if self.has_token(n):
            tok = self.tokens[self.pos + n]

            if value is not None:
                if isinstance(value, str):
                    if tok.value != value:
                        return False
                else:
                    if tok.value not in value:
                        return False

            return tok.type in type_

        return False

    def lookahead_line(self, n: int = 1) -> int:
        if self.has_token(n):
            return self.tokens[self.pos + n].pos.line

        return -1

    def parse_Statement(self) -> Node:
        tok = self.next_token()

        match tok.type:
            case TokenType.KEYWORD:
                if tok.value in Token.TYPES:
                    name = self.next_token(TokenType.ID)
                    if self.lookahead_token(TokenType.SET, "="):
                        self.next_token(TokenType.SET, "=")
                        value = self.parse_Value()
                        return DeclarationNode(tok.pos + name.pos,
                                               VariableValue(Type[tok.value.upper()], name.value), value)

                    return DeclarationNode(tok.pos + name.pos,
                                           VariableValue(Type[tok.value.upper()], name.value), None)

                elif tok.value in Token.BLOCK_STATEMENTS:
                    self.prev_token()
                    return self.parse_BlockStatement()

                match tok.value:
                    case "return":
                        if len(self.function_stack) > 0:
                            if self.lookahead_line() == tok.pos.line:
                                value = self.parse_Value()
                                return ReturnNode(tok.pos + value.get_pos(), self.function_stack[-1], value)
                            return ReturnNode(tok.pos, self.function_stack[-1], None)
                        parse_error(tok.pos, "Return statement used outside of a function")

                    case "break":
                        if len(self.loop_stack) > 0:
                            return BreakNode(tok.pos, self.loop_stack[-1])
                        parse_error(tok.pos, "Break statement used outside of a function")

                    case "continue":
                        if len(self.loop_stack) > 0:
                            return ContinueNode(tok.pos, self.loop_stack[-1])
                        parse_error(tok.pos, "Continue statement used outside of a function")

                    case "end":
                        return EndNode(tok.pos)

            case TokenType.ID:
                if self.lookahead_token(TokenType.SET):
                    op = self.next_token(TokenType.SET)
                    value = self.parse_Value()
                    return AssignmentNode(tok.pos + value.get_pos(), tok.value, op.value, value)\

                elif self.lookahead_token(TokenType.LPAREN):
                    self.next_token(TokenType.LPAREN)
                    return CallNode(tok.pos, tok.value, self.parse_funcArgVals())

                elif self.lookahead_token(TokenType.LBRACK):
                    index = self.parse_Value()
                    self.next_token(TokenType.RBRACK)

                    op = self.next_token(TokenType.SET)

                    value = self.parse_Value()

                    return IndexedAssignmentNode(tok.pos + value.get_pos(), tok.value, index, op.value, value)

        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

    def parse_BlockStatement(self) -> IfNode | LoopNode | FunctionNode:
        tok = self.next_token(TokenType.ID)
        self.next_token(TokenType.LPAREN)

        match tok.value:
            case "if":
                cond = self.parse_Value()
                self.next_token(TokenType.RPAREN)

                self.next_token(TokenType.LBRACE)
                code = self.parse_CodeBlock()

                if self.lookahead_token(TokenType.KEYWORD, "else"):
                    self.next_token(TokenType.KEYWORD)
                    self.next_token(TokenType.LBRACE)

                    return IfNode(tok.pos, cond, code, self.parse_CodeBlock())

                return IfNode(tok.pos, cond, code, None)

            case "while":
                cond = self.parse_Value()
                self.next_token(TokenType.RPAREN)

                self.next_token(TokenType.LBRACE)

                return WhileNode(tok.pos, self.loop_name(), cond, self.parse_CodeBlock())

            case "for":
                if self.lookahead_token(TokenType.ID) and self.lookahead_token(TokenType.COLON, None, 2):
                    var = self.next_token(TokenType.ID)
                    self.next_token(TokenType.COLON)
                    until = self.parse_Value()
                    self.next_token(TokenType.RPAREN)

                    self.next_token(TokenType.LBRACE)

                    return RangeNode(tok.pos, self.loop_name(), var.value, until, self.parse_CodeBlock())

                init = self.parse_Statement()
                self.next_token(TokenType.SEMICOLON)
                cond = self.parse_Value()
                self.next_token(TokenType.SEMICOLON)
                action = self.parse_Statement()
                self.next_token(TokenType.RPAREN)

                self.next_token(TokenType.LBRACE)

                return ForNode(tok.pos, self.loop_name(), init, cond, action, self.parse_CodeBlock())

            case "function":
                name = self.next_token(TokenType.ID)
                self.next_token(TokenType.LPAREN)
                params = self.parse_funcArgVars()

                self.next_token(TokenType.LBRACE)
                self.function_stack.append(name.value)
                code = self.parse_CodeBlock()
                self.function_stack.pop(-1)

                return FunctionNode(tok.pos, name.value, params, code)

    def parse_CodeBlock(self):
        code = []
        while self.has_token():
            if self.lookahead_token(TokenType.RBRACE):
                break

            code.append(self.parse_Statement())

        return CodeBlockNode(code)

    def parse_funcArgVars(self) -> list[tuple[str, Type]]:
        variables = []

        last_tok = TokenType.LPAREN
        type_ = None
        while self.has_token():
            tok = self.next_token()

            match tok.type:
                case TokenType.RPAREN:
                    if last_tok in TokenType.COMMA | TokenType.KEYWORD:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

                    break

                case TokenType.COMMA:
                    if last_tok != TokenType.ID:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

                case TokenType.KEYWORD:
                    if last_tok in TokenType.ID | TokenType.KEYWORD or tok.value not in Token.TYPES:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)
                    type_ = Type[tok.value.upper()]

                case TokenType.ID:
                    if last_tok != TokenType.KEYWORD:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

                    variables.append((tok.value, type_))

                case _:
                    parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

            last_tok = tok.type

        return variables

    def parse_funcArgVals(self) -> list[Node]:
        values = []

        last_tok = TokenType.LPAREN
        while self.has_token():
            tok = self.next_token()

            match tok.type:
                case TokenType.RPAREN:
                    if last_tok == TokenType.COMMA:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

                    break

                case TokenType.COMMA:
                    if last_tok != TokenType.ID:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

                    last_tok = TokenType.COMMA

                case _:
                    if last_tok == TokenType.ID:
                        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)

                    last_tok = TokenType.ID
                    self.prev_token()

                    values.append(self.parse_Value())

        return values

    def parse_binaryOp(self, operators: tuple, value_get: callable) -> BinaryOpNode:
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
            ("<", ">", "==", ">=", "!="),
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

    def parse_Call(self) -> CallNode | ValueNode | BinaryOpNode:
        if self.lookahead_token(TokenType.ID) and self.lookahead_token(TokenType.LPAREN, None, 2):
            name = self.next_token(TokenType.ID)
            self.next_token(TokenType.LPAREN)
            params = self.parse_funcArgVals()
            return CallNode(name.pos, name.value, params)

        return self.parse_Atom()

    def parse_Atom(self) -> ValueNode | BinaryOpNode:
        tok = self.next_token()

        match tok.type:
            case TokenType.ID:
                if tok.type == TokenType.ID and self.lookahead_token(TokenType.LBRACK):
                    self.next_token(TokenType.LBRACK)
                    index = self.parse_Value()
                    self.next_token(TokenType.RBRACK)

                    return IndexedValueNode(tok.pos + index.pos, tok.value, index)

                return VariableValueNode(tok.pos, tok.value)

            case TokenType.STRING:
                return StringValueNode(tok.pos, tok.value)

            case TokenType.NUMBER:
                try:
                    val = float(tok.value)
                except ValueError:
                    parse_error(tok.pos, ParseErrorType.INVALID_TOKEN)
                else:
                    if val.is_integer():
                        val = int(val)
                    return NumberValueNode(tok.pos, val)

            case TokenType.LPAREN:
                value = self.parse_Value()
                self.next_token(TokenType.RPAREN)

                return value

        parse_error(tok.pos, ParseErrorType.UNEXPECTED_TOKEN)