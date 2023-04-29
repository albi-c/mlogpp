import ast
import operator

from ..tokens import TokenType, Token
from ..generic_parser import GenericParser
from .node import *


class DeferredMathValue(Value):
    pass


class AsmParser(GenericParser):
    """
    Parse mlog++ assembly code.
    """

    VARIABLES = {}

    OPERATORS: dict[type] = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                             ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Pow: operator.pow,
                             ast.USub: operator.neg, ast.Not: operator.not_, ast.Mod: operator.mod,
                             ast.BitXor: operator.xor, ast.And: operator.and_, ast.Or: operator.or_,
                             ast.BitAnd: operator.and_, ast.BitOr: operator.or_, ast.Eq: operator.eq,
                             ast.Gt: operator.gt, ast.GtE: operator.ge, ast.Lt: operator.lt, ast.LtE: operator.le,
                             ast.NotEq: operator.ne, ast.LShift: operator.lshift, ast.RShift: operator.rshift}

    @staticmethod
    def op_eval(node):
        """
        Evaluate constant expression.

        Args:
            node: AST node

        Returns:
            Result of the expression
        """

        if isinstance(node, list):
            for n in node:
                return AsmParser.op_eval(n)

            raise RuntimeError(f"Eval error {node}")

        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.BinOp):
            if (op := AsmParser.OPERATORS.get(type(node.op))) is None:
                raise RuntimeError("Eval error {node}")
            return op(AsmParser.op_eval(node.left), AsmParser.op_eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            if (op := AsmParser.OPERATORS.get(type(node.op))) is None:
                raise RuntimeError("Eval error {node}")
            return op(AsmParser.op_eval(node.operand))
        elif isinstance(node, ast.Assign):
            value = AsmParser.op_eval(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    AsmParser.VARIABLES[target.id] = value
                else:
                    raise RuntimeError(f"Eval error {node}")
            return value
        elif isinstance(node, ast.Name):
            return AsmParser.VARIABLES[node.id]
        else:
            raise RuntimeError(f"Eval error {node}")

    def _init(self):
        # convert keyword and builtin tokens into id tokens
        for tok in self.tokens:
            if tok.type in (TokenType.KEYWORD, TokenType.NATIVE):
                tok.type = TokenType.ID

    def parse_CodeBlock(self, name: str | None, end_at_rbrace: bool = True) -> CodeBlockNode:
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

            s = self.parse_Statement()
            if s is not None:
                code.append(s)

        return CodeBlockNode(code, name)

    def parse_Statement(self) -> Node | None:
        n = self.next_token()

        if n.type == TokenType.ID:
            if self.lookahead_token(TokenType.SET):
                op = self.next_token(TokenType.SET)
                if op.value == "=":
                    if self.lookahead_token(TokenType.ID) and self.lookahead_token(TokenType.LBRACK, None, 2):
                        cell = self.next_token(TokenType.ID)
                        self.next_token(TokenType.LBRACK)
                        index = self.parse_Value()
                        self.next_token(TokenType.RBRACK)
                        return CellReadNode(n.pos + op.pos, cell.value, index, n.value)

                    self.prev_token(2)
                    return self.parse_Operation()
                else:
                    return AssignmentNode(n.pos + op.pos, n.value, op.value, self.parse_Value())

            elif self.lookahead_token(TokenType.LPAREN) and n.value in MInstructionType.INSTRUCTION_NAMES:
                self.prev_token(1)
                return self.parse_Call()

            elif self.lookahead_token(TokenType.COLON):
                self.next_token(TokenType.COLON)
                return LabelNode(n.pos, n.value)

            elif self.lookahead_token(TokenType.LBRACK):
                self.next_token(TokenType.LBRACK)
                index = self.parse_Value()
                self.next_token(TokenType.RBRACK)
                op = self.next_token(TokenType.SET, "=")
                return CellWriteNode(n.pos + op.pos, n.value, index, self.parse_Value())

        elif n.type == TokenType.COLON:
            if self.lookahead_token(TokenType.ID):
                label = self.next_token(TokenType.ID)
                if self.lookahead_token(TokenType.LPAREN):
                    self.next_token(TokenType.LPAREN)
                    a = self.parse_Value()
                    op = self.next_token(TokenType.OPERATOR)
                    b = self.parse_Value()
                    self.next_token(TokenType.RPAREN)
                    return JumpNode(n.pos, label.value, (op.value, a, b))
                else:
                    return JumpNode(n.pos + label.pos, label.value, ("always", NullValue(), NullValue()))

        elif n.type == TokenType.LBRACE:
            self.prev_token(1)
            self.parse_ConstValue()
            return None

        Error.unexpected_token(n)

    def parse_Value(self) -> Value:
        n = self.next_token(TokenType.ID | TokenType.NUMBER | TokenType.STRING | TokenType.LBRACE)
        if n.type == TokenType.ID:
            return VariableValue(Type.ANY, n.value)
        elif n.type == TokenType.NUMBER:
            try:
                return NumberValue(int(n.value))
            except ValueError:
                return NumberValue(float(n.value))
        elif n.type == TokenType.STRING:
            return StringValue(n.value)
        elif n.type == TokenType.LBRACE:
            self.prev_token(1)
            return Value.from_(self.parse_ConstValue())

        raise RuntimeError("Internal error")

    def parse_ConstValue(self, default: int | float | None = None) -> int | float:
        if default is not None and not self.lookahead_token(TokenType.LBRACE):
            return default

        start = self.next_token(TokenType.LBRACE)

        expr = ""
        mode = "eval"
        while self.has_token() and not self.lookahead_token(TokenType.RBRACE):
            tok = self.next_token(TokenType.NUMBER | TokenType.OPERATOR | TokenType.LPAREN | TokenType.RPAREN |
                                  TokenType.SET | TokenType.ID | TokenType.STRING)

            if tok.type == TokenType.SET:
                if tok.value != "=":
                    Error.unexpected_token(tok)

                mode = "exec"

            if tok.value in ("===", "!==="):
                expr += tok.value[:-1]
            else:
                expr += tok.value

        if expr.strip():
            try:
                val = AsmParser.op_eval(ast.parse(expr, mode=mode).body)
            except ArithmeticError:
                Error.custom(start.pos, f"Arithmetic error in const expression [{expr}]")
                return 0
            except (NameError, KeyError):
                Error.custom(start.pos, f"Variable not found in const expression [{expr}]")
                return 0
            except (RuntimeError, TypeError, Exception):
                Error.custom(start.pos, f"Invalid const expression [{expr}]")
                return 0

        else:
            val = 0

        self.next_token(TokenType.RBRACE)

        return val

    def parse_Operation(self) -> Node:
        var = self.next_token(TokenType.ID)
        self.next_token(TokenType.SET, "=")

        if self.lookahead_token(TokenType.OPERATOR):
            op = self.next_token(TokenType.OPERATOR).value
            a = self.parse_Value()

            return UnaryOpNode(var.pos, var.value, op, a)

        a = self.parse_Value()

        if self.lookahead_token(TokenType.OPERATOR):
            op = self.next_token(TokenType.OPERATOR).value
            b = self.parse_Value()

            return BinaryOpNode(var.pos, var.value, a, op, b)

        else:
            return AssignmentNode(var.pos, var.value, "=", a)

    def parse_Call(self) -> Node:
        name = self.next_token(TokenType.ID)
        self.next_token(TokenType.LPAREN)

        values = []
        last_tok = TokenType.LPAREN
        while self.has_token():
            tok = self.next_token()

            if tok.type == TokenType.RPAREN:
                if last_tok == TokenType.COMMA:
                    Error.unexpected_token(tok)

                break

            elif tok.type == TokenType.COMMA:
                if last_tok != TokenType.ID:
                    Error.unexpected_token(tok)

                last_tok = TokenType.COMMA

            else:
                if last_tok == TokenType.ID:
                    Error.unexpected_token(tok)

                last_tok = TokenType.ID
                self.prev_token()

                values.append(self.parse_Value())

        return CallNode(name.pos, name.value, values)
