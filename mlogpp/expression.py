import ast
import operator

from .util import Position
from .tokens import TokenType
from .error import Error


class Expression:
    variables: dict[str] = {}

    return_stack: list = []

    TOKENS: TokenType = TokenType.ID | TokenType.STRING | TokenType.SET | TokenType.OPERATOR | TokenType.NUMBER | \
                        TokenType.LPAREN | TokenType.RPAREN | TokenType.SEMICOLON | TokenType.KEYWORD | \
                        TokenType.LBRACK | TokenType.RBRACK | TokenType.COMMA | TokenType.COLON

    OPERATORS: dict[type] = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                             ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Pow: operator.pow,
                             ast.USub: operator.neg, ast.Not: operator.not_, ast.Mod: operator.mod,
                             ast.BitXor: operator.xor, ast.And: operator.and_, ast.Or: operator.or_,
                             ast.BitAnd: operator.and_, ast.BitOr: operator.or_, ast.Eq: operator.eq,
                             ast.Gt: operator.gt, ast.GtE: operator.ge, ast.Lt: operator.lt, ast.LtE: operator.le,
                             ast.NotEq: operator.ne, ast.LShift: operator.lshift, ast.RShift: operator.rshift}

    BUILTINS: dict[str] = {"range": range, "map": map, "str": str, "list": list, "int": int, "float": float,
                           "print": lambda *x: print("EXPRESSION:", *x)}

    @staticmethod
    def exec(pos: Position, expr: str) -> list[str | int | float | list | None]:
        expr = expr.replace("\" \"", "\"\"").replace("f \"", "f\"")
        if expr.strip():
            try:
                return Expression.op_eval(ast.parse(expr, mode="exec").body)
            except ArithmeticError:
                Error.custom(pos, f"Arithmetic error in const expression [{expr}]")
            except IndexError:
                Error.custom(pos, f"Index error in const expression [{expr}]")
            except (NameError, KeyError):
                Error.custom(pos, f"Variable not found in const expression [{expr}]")
            except (RuntimeError, AssertionError, TypeError, Exception):
                Error.custom(pos, f"Invalid const expression [{expr}]")

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
    def op_eval(node, overrides: dict[str] = None):
        """
        Evaluate constant expression.

        Args:
            node: AST node
            overrides: Local variable overrides

        Returns:
            Result of the expression
        """

        if node is None:
            return None

        if overrides is None:
            overrides = {}

        if isinstance(node, list):
            values = []
            for n in node:
                values.append(Expression.op_eval(n, overrides))

            return values

        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.JoinedStr):
            return "".join([str(Expression.op_eval(val, overrides)) for val in node.values])
        elif isinstance(node, ast.FormattedValue):
            assert node.format_spec is None
            assert node.conversion == -1
            return Expression.op_eval(node.value, overrides)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Compare):
            all_true = True
            for op, cmp in zip(node.ops, node.comparators):
                if (op_ := Expression.OPERATORS.get(type(op))) is None:
                    raise RuntimeError(f"Eval error {node}")
                all_true = all_true and Expression.coerce(op_,Expression.op_eval(node.left, overrides), Expression.op_eval(cmp, overrides))
            return all_true
        elif isinstance(node, ast.BinOp):
            if (op := Expression.OPERATORS.get(type(node.op))) is None:
                raise RuntimeError(f"Eval error {node}")
            return Expression.coerce(op, Expression.op_eval(node.left, overrides), Expression.op_eval(node.right, overrides))
        elif isinstance(node, ast.UnaryOp):
            if (op := Expression.OPERATORS.get(type(node.op))) is None:
                raise RuntimeError(f"Eval error {node}")
            return op(Expression.op_eval(node.operand, overrides))
        elif isinstance(node, ast.Assign):
            value = Expression.op_eval(node.value, overrides)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    Expression.variables[target.id] = value
                else:
                    raise RuntimeError(f"Eval error {node}")
            return None
        elif isinstance(node, ast.Name):
            if node.id in Expression.BUILTINS:
                return Expression.BUILTINS[node.id]
            if node.id in overrides:
                return overrides[node.id]
            return Expression.variables[node.id]
        elif isinstance(node, ast.Expr):
            return Expression.op_eval(node.value, overrides)
        elif isinstance(node, ast.IfExp):
            if Expression.op_eval(node.test):
                return Expression.op_eval(node.body, overrides)
            else:
                return Expression.op_eval(node.orelse, overrides)
        elif isinstance(node, ast.ListComp):
            if len(node.generators) != 1:
                raise RuntimeError(f"Eval error {node}")

            comp = node.generators[0]
            assert isinstance(comp, ast.comprehension)
            name = comp.target
            assert isinstance(name, ast.Name)
            name = name.id
            seq = Expression.op_eval(comp.iter, overrides)

            lst = []
            for elem in seq:
                overrides_ = overrides | {name: elem}
                if not all(Expression.op_eval(cond, overrides_) for cond in comp.ifs):
                    continue

                lst.append(Expression.op_eval(node.elt, overrides_))

            return lst
        elif isinstance(node, ast.Call):
            assert len(node.keywords) == 0
            func = Expression.op_eval(node.func, overrides)
            return func(*[Expression.op_eval(val, overrides) for val in node.args])
        elif isinstance(node, ast.List):
            return [Expression.op_eval(val, overrides) for val in node.elts]
        elif isinstance(node, ast.Subscript):
            return Expression.op_eval(node.value, overrides).__getitem__(Expression.op_eval(node.slice, overrides))
        elif isinstance(node, ast.Slice):
            return slice(Expression.op_eval(node.lower, overrides), Expression.op_eval(node.upper, overrides),
                         Expression.op_eval(node.step, overrides))
        elif isinstance(node, ast.Attribute):
            val = Expression.op_eval(node.value, overrides)
            if isinstance(val, str):
                if node.attr == "join":
                    return val.join
                elif node.attr == "replace":
                    return val.replace
            raise RuntimeError(f"Eval error {node}")
        elif isinstance(node, ast.FunctionDef):
            assert len(node.args.posonlyargs) == 0
            assert len(node.args.kwonlyargs) == 0
            assert len(node.args.kw_defaults) == 0
            assert len(node.args.defaults) == 0

            def func(*args):
                if len(args) != len(node.args.args):
                    raise TypeError("Invalid argument count")

                Expression.return_stack.append(None)

                Expression.op_eval(node.body, overrides | {
                    arg.arg: args[i] for i, arg in enumerate(node.args.args)
                })

                return Expression.return_stack.pop(-1)

            Expression.variables[node.name] = func
        elif isinstance(node, ast.Return):
            Expression.return_stack[-1] = Expression.op_eval(node.value, overrides)
        else:
            raise RuntimeError(f"Eval error {node}")
