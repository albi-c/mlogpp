from .tokens import TokenType, Token
from .node import *
from .generic_parser import GenericParser
from .asm.parser import AsmParser

from typing import Callable


class Parser(GenericParser):
    """
    Parses mlog++ code.
    """

    def _init(self):
        self.const_expressions = True
        self.token_preprocess_start = TokenType.DOLLAR

    def parse_CodeBlock(self, end_at_rbrace: bool, create_scope: bool = False) -> Node:
        pos = None
        code = []
        end_by_rbrace = False
        while self.has_token():
            if pos is None:
                pos = self.next_token().pos
            else:
                pos += self.next_token().pos
            self.prev_token()

            if end_at_rbrace and self.lookahead_token(TokenType.RBRACE):
                end_by_rbrace = True
                break

            code.append(self.parse_Statement())

        if end_at_rbrace and not end_by_rbrace:
            Error.unexpected_eof(pos)

        return BlockNode(pos, code, scope=create_scope)

    def parse_AsmCodeBlock(self) -> Node:
        self.next_token(TokenType.LBRACE)

        tokens = []

        depth = 1
        while self.has_token():
            if self.lookahead_token(TokenType.LBRACE):
                depth += 1
            elif self.lookahead_token(TokenType.RBRACE):
                depth -= 1
                if depth == 0:
                    self.next_token()
                    break

            tokens.append(self.next_token())

        return AsmParser().parse(tokens)

    def parse_Statement(self) -> Node:
        if self.lookahead_token(TokenType.KEYWORD, "asm"):
            self.next_token()

            return self.parse_inlineAsm()

        elif self.lookahead_token(TokenType.ID) and self.lookahead_token(TokenType.ID, None, 2):
            type_ = self.next_token()
            name = self.next_token()

            if self.lookahead_token(TokenType.SET, "="):
                self.next_token()
                value = self.parse_Value()

                return DeclarationNode(type_.pos + value.get_pos(), type_.value, name.value, value)

            else:
                names = [name.value]
                pos = type_.pos + name.pos
                while self.lookahead_token(TokenType.COMMA):
                    self.next_token()
                    name = self.next_token(TokenType.ID)
                    names.append(name.value)
                    pos += name.pos
                return MultiDeclarationNode(pos, type_.value, names)

        elif self.lookahead_token(TokenType.KEYWORD):
            tok = self.next_token()

            if tok.value in Token.BLOCK_STATEMENTS:
                self.prev_token()
                return self.parse_BlockStatement()

            match tok.value:
                case "return":
                    value = None

                    if self.has_token() and self.next_token().pos.line == tok.pos.line:
                        self.prev_token()
                        value = self.parse_Value()
                    else:
                        self.prev_token()

                    return ReturnNode(tok.pos + (value.get_pos() if value is not None else tok.pos), value)

                case "break":
                    return BreakNode(tok.pos)

                case "continue":
                    return ContinueNode(tok.pos)

                case "configuration":
                    if self.lookahead_token(TokenType.SET, n=2):
                        type_ = "let"
                    else:
                        type_ = self.next_token(TokenType.ID).value
                    name = self.next_token(TokenType.ID)
                    self.next_token(TokenType.SET)
                    value = self.parse_Value()

                    return ConfigNode(tok.pos + value.get_pos(), type_, name.value, value)

                case "const":
                    if self.lookahead_token(TokenType.SET, "=", n=2):
                        name = self.next_token(TokenType.ID)
                        self.next_token()
                        value = self.parse_Value()

                        return DeclarationNode(tok.pos + value.get_pos(), "let", name.value, value, const_on_write=True)

                    type_ = self.next_token(TokenType.ID).value
                    name = self.next_token(TokenType.ID)

                    if self.lookahead_token(TokenType.SET, "="):
                        self.next_token()
                        value = self.parse_Value()

                        return DeclarationNode(tok.pos + value.get_pos(), type_, name.value, value, const_on_write=True)

                    else:
                        names = [name.value]
                        pos = tok.pos + name.pos
                        while self.lookahead_token(TokenType.COMMA):
                            self.next_token()
                            name = self.next_token(TokenType.ID)
                            names.append(name.value)
                            pos += name.pos

                        return MultiDeclarationNode(pos, type_, names, const_on_write=True)


            raise RuntimeError("invalid keyword")

        elif self.lookahead_token(TokenType.LBRACE):
            self.next_token()
            return self.parse_CodeBlock(True, create_scope=True)

        return self.parse_Value()

    def parse_inlineAsm(self) -> Node:
        inputs = []
        if self.lookahead_token(TokenType.LPAREN):
            self.next_token()

            last = TokenType.LPAREN
            while self.has_token():
                tok = self.next_token()

                if tok.type == TokenType.RPAREN:
                    if last == TokenType.COMMA:
                        Error.unexpected_token(tok)

                    break

                elif tok.type == TokenType.ID:
                    if last == TokenType.ID:
                        Error.unexpected_token(tok)

                    inputs.append(tok.value)
                    last = TokenType.ID

                elif tok.type == TokenType.COMMA:
                    if last == TokenType.COMMA:
                        Error.unexpected_token(tok)

                    last = TokenType.COMMA

                else:
                    Error.unexpected_token(tok)

        outputs = []
        if self.lookahead_token(TokenType.ARROW):
            self.next_token()
            self.next_token(TokenType.LPAREN)

            last = TokenType.LPAREN
            while self.has_token():
                tok = self.next_token()

                if tok.type == TokenType.RPAREN:
                    if last == TokenType.COMMA:
                        Error.unexpected_token(tok)

                    break

                elif tok.type == TokenType.ID:
                    if last == TokenType.ID:
                        Error.unexpected_token(tok)

                    outputs.append(tok.value)
                    last = TokenType.ID

                elif tok.type == TokenType.COMMA:
                    if last == TokenType.COMMA:
                        Error.unexpected_token(tok)

                    last = TokenType.COMMA

                else:
                    Error.unexpected_token(tok)

        block = self.parse_AsmCodeBlock()
        return AsmBlockNode(block.get_pos(), block, inputs, outputs)

    def parse_if(self) -> tuple[Node, Node, Position]:
        self.next_token(TokenType.LPAREN)
        condition = self.parse_Value()
        self.next_token(TokenType.RPAREN)

        self.next_token(TokenType.LBRACE)
        code = self.parse_CodeBlock(True)
        end = self.next_token(TokenType.RBRACE)

        return condition, code, end.pos

    def parse_BlockStatement(self) -> Node:
        tok = self.next_token(TokenType.KEYWORD)

        match tok.value:
            case "if":
                condition, code, end_pos = self.parse_if()

                node = IfNode(tok.pos + end_pos, condition, code, None)
                inner_node = node

                while self.lookahead_token(TokenType.KEYWORD, "elif"):
                    tok = self.next_token()
                    condition, code, end_pos = self.parse_if()

                    inner_node.else_code = IfNode(tok.pos + end_pos, condition, code, None)
                    inner_node = inner_node.else_code

                if self.lookahead_token(TokenType.KEYWORD, "else"):
                    self.next_token()

                    self.next_token(TokenType.LBRACE)
                    code = self.parse_CodeBlock(True)
                    self.next_token(TokenType.RBRACE)

                    inner_node.else_code = code

                return node

            case "elif", "else":
                Error.unexpected_token(tok)

            case "while":
                self.next_token(TokenType.LPAREN)
                condition = self.parse_Value()
                self.next_token(TokenType.RPAREN)

                self.next_token(TokenType.LBRACE)
                code = self.parse_CodeBlock(True)
                end = self.next_token(TokenType.RBRACE)

                return WhileNode(tok.pos + end.pos, condition, code)

            case "for":
                self.next_token(TokenType.LPAREN)

                if self.lookahead_token(TokenType.ID) and self.lookahead_token(TokenType.COLON, None, 2):
                    name = self.next_token()
                    self.next_token()
                    a = self.parse_Value()
                    b = None
                    if self.lookahead_token(TokenType.OPERATOR, ".."):
                        self.next_token()
                        b = self.parse_Value()
                    self.next_token(TokenType.RPAREN)

                    self.next_token(TokenType.LBRACE)
                    code = self.parse_CodeBlock(True)
                    end = self.next_token(TokenType.RBRACE)

                    return RangeNode(tok.pos + end.pos, name.value, a, b, code)

                init = self.parse_Statement()
                self.next_token(TokenType.SEMICOLON)
                condition = self.parse_Value()
                self.next_token(TokenType.SEMICOLON)
                action = self.parse_Value()
                self.next_token(TokenType.RPAREN)

                self.next_token(TokenType.LBRACE)
                code = self.parse_CodeBlock(True)
                end = self.next_token(TokenType.RBRACE)

                return ForNode(tok.pos + end.pos, init, condition, action, code)

            case "function":
                self.prev_token()
                return self.parse_Function()

            case "struct":
                name = self.next_token(TokenType.ID)

                parents = []
                if self.lookahead_token(TokenType.COLON):
                    self.next_token()
                    parents.append(self.next_token(TokenType.ID).value)
                    while self.lookahead_token(TokenType.COMMA):
                        self.next_token()
                        parents.append(self.next_token(TokenType.ID).value)

                self.next_token(TokenType.LBRACE)
                fields, functions = self.parse_structFields(name.value)
                end = self.next_token(TokenType.RBRACE)

                return StructNode(tok.pos + end.pos, name.value, fields, functions, parents)

        raise RuntimeError("invalid keyword")

    def parse_Function(self) -> FunctionNode:
        tok = self.next_token()
        name = self.next_token(TokenType.ID)
        self.next_token(TokenType.LPAREN)
        params = self.parse_funcParamsVars()
        self.next_token(TokenType.RPAREN)

        type_ = "null"
        if self.lookahead_token(TokenType.ARROW):
            self.next_token()
            type_ = self.next_token(TokenType.ID).value

        self.next_token(TokenType.LBRACE)
        code = self.parse_CodeBlock(True)
        end = self.next_token(TokenType.RBRACE)

        return FunctionNode(tok.pos + end.pos, name.value, params, type_, code)

    def parse_MemberFunction(self, typename: str) -> MemberFunctionNode:
        tok = self.next_token()
        name = self.next_token(TokenType.ID)
        self.next_token(TokenType.LPAREN)
        params = self.parse_memberFuncParamsVars(typename)
        self.next_token(TokenType.RPAREN)

        type_ = "null"
        if self.lookahead_token(TokenType.ARROW):
            self.next_token()
            type_ = self.next_token(TokenType.ID).value

        self.next_token(TokenType.LBRACE)
        code = self.parse_CodeBlock(True)
        end = self.next_token(TokenType.RBRACE)

        return MemberFunctionNode(tok.pos + end.pos, typename, name.value, params, type_, code)

    def parse_structFields(self, typename: str) -> tuple[list[tuple[str, str]], list[MemberFunctionNode]]:
        fields = []
        functions = []
        while not self.lookahead_token(TokenType.RBRACE):
            if self.lookahead_token(TokenType.KEYWORD, "function"):
                functions.append(self.parse_MemberFunction(typename))
                continue

            type_ = self.next_token(TokenType.ID).value

            fields.append((type_, self.next_token(TokenType.ID).value))

            while self.lookahead_token(TokenType.COMMA):
                self.next_token(TokenType.COMMA)
                fields.append((type_, self.next_token(TokenType.ID).value))

        return fields, functions

    def parse_binaryOp(self, operators: tuple[str, ...], lower_func: Callable[[], Node],
                       token_type: TokenType = TokenType.OPERATOR, invert: bool = False) -> Node:

        if invert:
            node = lower_func()

            operations = []
            while self.has_token():
                if self.lookahead_token(token_type, operators):
                    op = self.next_token()
                    right = lower_func()
                    operations.append((op, right))

                else:
                    break

            for i, [op, right] in enumerate(reversed(operations)):
                if i >= 1:
                    left = operations[i + 1][1]
                    node = BinaryOpNode(left.get_pos() + right.get_pos(), left, op.value, right)

                else:
                    node = BinaryOpNode(node.get_pos() + right.get_pos(), node, op.value, right)

            return node

        else:
            node = lower_func()

            while self.has_token():
                if self.lookahead_token(token_type, operators):
                    op = self.next_token()
                    right = lower_func()
                    node = BinaryOpNode(node.get_pos() + right.get_pos(), node, op.value, right)

                else:
                    break

            return node

    def parse_unaryOp(self, operators: tuple[str, ...], lower_func: Callable[[], Node],
                      token_type: TokenType = TokenType.OPERATOR) -> Node:

        operations = []
        while self.has_token():
            if self.lookahead_token(token_type, operators):
                op = self.next_token()
                operations.append(op)

            else:
                break

        node = lower_func()

        for op in reversed(operations):
            node = UnaryOpNode(op.pos + node.get_pos(), op.value, node)

        return node

    def parse_Value(self) -> Node:
        if self.lookahead_token(TokenType.KEYWORD):
            tok = self.next_token()

            if tok.value in Token.BLOCK_STATEMENTS:
                self.prev_token()
                return self.parse_BlockStatement()

            Error.unexpected_token(tok)

        return self.parse_Assignment()

    def parse_Assignment(self) -> Node:
        return self.parse_binaryOp(
            ("=", "+=", "-=", "%=", "&=", "|=", "^=", "*=", "/=", "**=", "//=", "<<=", ">>="),
            self.parse_OrTest,
            TokenType.SET,
            True
        )

    def parse_OrTest(self) -> Node:
        return self.parse_binaryOp(
            ("||",),
            self.parse_AndTest
        )

    def parse_AndTest(self) -> Node:
        return self.parse_binaryOp(
            ("&&",),
            self.parse_NotTest
        )

    def parse_NotTest(self) -> Node:
        return self.parse_unaryOp(
            ("!",),
            self.parse_Comparison
        )

    def parse_Comparison(self) -> Node:
        return self.parse_binaryOp(
            ("<", ">", "==", "===", ">=", "!="),
            self.parse_OrExpr
        )

    def parse_OrExpr(self) -> Node:
        return self.parse_binaryOp(
            ("|",),
            self.parse_XorExpr
        )

    def parse_XorExpr(self) -> Node:
        return self.parse_binaryOp(
            ("^",),
            self.parse_AndExpr
        )

    def parse_AndExpr(self) -> Node:
        return self.parse_binaryOp(
            ("&",),
            self.parse_ShiftExpr
        )

    def parse_ShiftExpr(self) -> Node:
        return self.parse_binaryOp(
            ("<<", ">>"),
            self.parse_ArithExpr
        )

    def parse_ArithExpr(self) -> Node:
        return self.parse_binaryOp(
            ("+", "-"),
            self.parse_Term
        )

    def parse_Term(self) -> Node:
        return self.parse_binaryOp(
            ("*", "/", "//", "%"),
            self.parse_Factor
        )

    def parse_Factor(self) -> Node:
        return self.parse_unaryOp(
            ("-", "~"),
            self.parse_Power
        )

    def parse_Power(self) -> Node:
        return self.parse_binaryOp(
            ("**",),
            self.parse_Call
        )

    def parse_Call(self) -> Node:
        node = self.parse_Index()

        while self.lookahead_token(TokenType.LPAREN):
            self.next_token()
            params = self.parse_funcParamsValues()
            end = self.next_token(TokenType.RPAREN)

            node = CallNode(node.get_pos() + end.pos, node, params)

        return node

    def parse_Index(self) -> Node:
        node = self.parse_Attr()

        while self.lookahead_token(TokenType.LBRACK):
            self.next_token()
            index = self.parse_Value()
            end = self.next_token(TokenType.RBRACK)

            node = IndexNode(node.get_pos() + end.pos, node, index)

        return node

    def parse_Attr(self) -> Node:
        node = self.parse_Atom()

        while self.has_token():
            if self.lookahead_token(TokenType.OPERATOR, "."):
                self.next_token()
                attr = self.next_token(TokenType.ID)
                node = AttributeNode(node.get_pos() + attr.pos, node, attr.value)

            else:
                break

        return node

    def parse_Atom(self) -> Node:
        tok = self.next_token()

        match tok.type:
            case TokenType.ID:
                return VariableValueNode(tok.pos, tok.value)

            case TokenType.NUMBER:
                return NumberValueNode(tok.pos, float(tok.value))

            case TokenType.STRING:
                return StringValueNode(tok.pos, tok.value)

            case TokenType.LPAREN:
                val = self.parse_Value()
                end = self.next_token(TokenType.RPAREN)
                val.pos = tok.pos + end.pos
                return val

            case TokenType.OPERATOR:
                if tok.value == "%" and self.lookahead_token(TokenType.ID):
                    col = self.next_token(TokenType.ID)
                    if col.value.startswith("_") and len(col.value) > 1:
                        return ColorValueNode(tok.pos + col.pos, "%" + col.value[1:])

        Error.unexpected_token(tok)

    def parse_funcParamsValues(self) -> list[Node]:
        params = []

        last_tok = TokenType.LPAREN

        while self.has_token():
            if self.lookahead_token(TokenType.RPAREN):
                if last_tok == TokenType.COMMA:
                    Error.unexpected_token(self.next_token())

                break

            elif self.lookahead_token(TokenType.COMMA):
                tok = self.next_token()

                if last_tok != TokenType.ID:
                    Error.unexpected_token(tok)

                last_tok = TokenType.COMMA

            else:
                if last_tok == TokenType.ID:
                    Error.unexpected_token(self.next_token())

                if self.lookahead_token(TokenType.ID) and self.lookahead_token(TokenType.COLON, n=2):
                    name = self.next_token()
                    self.next_token()

                    if self.lookahead_token(TokenType.KEYWORD, "const"):
                        self.next_token()
                        const = True

                    else:
                        const = False

                    type_ = self.next_token()

                    params.append(DeclarationNode(type_.pos + name.pos, type_.value, name.value,
                                                  None, False, const_on_write=const))

                else:
                    params.append(self.parse_Value())

                last_tok = TokenType.ID

        return params

    def parse_funcParamsVars(self) -> list[tuple[str, str, bool]]:
        params = []

        last_tok = TokenType.LPAREN
        type_ = ""
        const = False
        while self.has_token():
            if self.lookahead_token(TokenType.RPAREN):
                if last_tok in TokenType.COMMA | TokenType.KEYWORD:
                    Error.unexpected_token(self.next_token())

                break

            elif self.lookahead_token(TokenType.COMMA):
                if last_tok != TokenType.ID:
                    Error.unexpected_token(self.next_token())

                self.next_token()

                last_tok = TokenType.COMMA

            elif self.lookahead_token(TokenType.ID) or self.lookahead_token(TokenType.KEYWORD, "const"):
                if last_tok == TokenType.KEYWORD:
                    params.append((type_, self.next_token().value, const))

                    const = False

                    last_tok = TokenType.ID

                elif last_tok in TokenType.LPAREN | TokenType.COMMA:
                    if self.lookahead_token(TokenType.KEYWORD, "const"):
                        self.next_token()
                        const = True
                    else:
                        type_ = self.next_token().value
                        last_tok = TokenType.KEYWORD

                else:
                    Error.unexpected_token(self.next_token())

            else:
                Error.unexpected_token(self.next_token())

        return params

    def parse_memberFuncParamsVars(self, typename: str) -> list[tuple[str, str, bool]]:
        params = []

        self_const = False
        if self.lookahead_token(TokenType.KEYWORD, "const"):
            self.next_token()
            self_const = True

        params.append((typename, self.next_token(TokenType.ID).value, self_const))

        last_tok = TokenType.ID
        type_ = ""
        const = False
        while self.has_token():
            if self.lookahead_token(TokenType.RPAREN):
                if last_tok in TokenType.COMMA | TokenType.KEYWORD:
                    Error.unexpected_token(self.next_token())

                break

            elif self.lookahead_token(TokenType.COMMA):
                if last_tok != TokenType.ID:
                    Error.unexpected_token(self.next_token())

                self.next_token()

                last_tok = TokenType.COMMA

            elif self.lookahead_token(TokenType.ID) or self.lookahead_token(TokenType.KEYWORD, "const"):
                if last_tok == TokenType.KEYWORD:
                    params.append((type_, self.next_token().value, const))

                    const = False

                    last_tok = TokenType.ID

                elif last_tok in TokenType.LPAREN | TokenType.COMMA:
                    if self.lookahead_token(TokenType.KEYWORD, "const"):
                        self.next_token()
                        const = True
                    else:
                        type_ = self.next_token().value
                        last_tok = TokenType.KEYWORD

                else:
                    Error.unexpected_token(self.next_token())

            else:
                Error.unexpected_token(self.next_token())

        return params
