import ast
import operator

from .util import Position
from .tokens import TokenType
from .error import Error


class Expression:
    variables: dict[str] = {}

    TOKENS: TokenType = TokenType.ID | TokenType.STRING | TokenType.SET | TokenType.OPERATOR | TokenType.NUMBER | \
                        TokenType.LPAREN | TokenType.RPAREN | TokenType.SEMICOLON

    OPERATORS: dict[type] = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                             ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Pow: operator.pow,
                             ast.USub: operator.neg, ast.Not: operator.not_, ast.Mod: operator.mod,
                             ast.BitXor: operator.xor, ast.And: operator.and_, ast.Or: operator.or_,
                             ast.BitAnd: operator.and_, ast.BitOr: operator.or_, ast.Eq: operator.eq,
                             ast.Gt: operator.gt, ast.GtE: operator.ge, ast.Lt: operator.lt, ast.LtE: operator.le,
                             ast.NotEq: operator.ne, ast.LShift: operator.lshift, ast.RShift: operator.rshift}

    @staticmethod
    def exec(pos: Position, expr: str) -> str | int | float | None:
        if expr.strip():
            try:
                return Expression.op_eval(ast.parse(expr, mode="exec").body)
            except ArithmeticError:
                Error.custom(pos, f"Arithmetic error in const expression [{expr}]")
                return 0
            except TypeError:
                Error.custom(pos, f"Type mismatch in const expression [{expr}]")
                return 0
            except (NameError, KeyError):
                Error.custom(pos, f"Variable not found in const expression [{expr}]")
                return 0
            except (RuntimeError, Exception):
                Error.custom(pos, f"Invalid const expression [{expr}]")
                return 0

        return 0

    @staticmethod
    def coerce(op, a, b):
        try:
            return op(a, b)
        except TypeError:
            if isinstance(a, int):
                if isinstance(b, str):
                    return op(str(a), b)

            elif isinstance(a, str):
                if isinstance(b, int):
                    return op(a, str(b))

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
            values = []
            for n in node:
                values.append(Expression.op_eval(n))

            return values

        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.BinOp):
            if (op := Expression.OPERATORS.get(type(node.op))) is None:
                raise RuntimeError("Eval error {node}")
            return Expression.coerce(op, Expression.op_eval(node.left), Expression.op_eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            if (op := Expression.OPERATORS.get(type(node.op))) is None:
                raise RuntimeError("Eval error {node}")
            return op(Expression.op_eval(node.operand))
        elif isinstance(node, ast.Assign):
            value = Expression.op_eval(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    Expression.variables[target.id] = value
                else:
                    raise RuntimeError(f"Eval error {node}")
            return value
        elif isinstance(node, ast.Name):
            return Expression.variables[node.id]
        elif isinstance(node, ast.Expr):
            return Expression.op_eval(node.value)
        elif isinstance(node, ast.IfExp):
            if Expression.op_eval(node.test):
                return Expression.op_eval(node.body)
            else:
                return Expression.op_eval(node.orelse)
        else:
            raise RuntimeError(f"Eval error {node}")
