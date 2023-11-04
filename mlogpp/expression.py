import ast
import operator
from typing import Any, Callable

from .util import Position
from .tokens import TokenType
from .error import Error


class Expression:
    scopes: list[dict[str, Any]]
    return_stack: list[Any]

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

    BUILTINS: dict[str, Any] = {"range": range, "map": map, "str": str, "list": list, "int": int, "float": float,
                                "print": lambda *x: print("EXPRESSION:", *x)}

    def __init__(self):
        self.scopes = [self.BUILTINS, {}]
        self.return_stack = []

    def scope_push(self):
        self.scopes.append({})

    def scope_pop(self):
        self.scopes.pop(-1)

    def scope_set(self, name: str, val: Any):
        self.scopes[-1][name] = val

    def scope_get(self, name: str) -> Any:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise NameError(name)

    def execute(self, pos: Position, expr: str) -> list[str | int | float | list | None]:
        new_expr = expr.replace("\" \"", "\"\"").replace("f \"", "f\"")
        if new_expr.strip():
            try:
                return self.eval(ast.parse(new_expr, mode="exec").body)
            except ArithmeticError:
                Error.custom(pos, f"Arithmetic error in const expression [{expr}]")
            except IndexError:
                Error.custom(pos, f"Index error in const expression [{expr}]")
            except (NameError, KeyError):
                Error.custom(pos, f"Variable not found in const expression [{expr}]")
            except (RuntimeError, AssertionError, TypeError, Exception):
                Error.custom(pos, f"Invalid const expression [{expr}]")

        return []

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

    def eval(self, node):
        if node is None:
            return None

        if isinstance(node, list):
            return list(map(self.eval, node))

        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.JoinedStr):
            return "".join([str(self.eval(val)) for val in node.values])
        elif isinstance(node, ast.FormattedValue):
            assert node.format_spec is None
            assert node.conversion == -1
            return self.eval(node.value)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Compare):
            all_true = True
            for op, cmp in zip(node.ops, node.comparators):
                if (op_ := self.OPERATORS.get(type(op))) is None:
                    raise RuntimeError(f"Eval error {node}")
                all_true = all_true and self.coerce(op_, self.eval(node.left), self.eval(cmp))
            return all_true
        elif isinstance(node, ast.BinOp):
            if (op := self.OPERATORS.get(type(node.op))) is None:
                raise RuntimeError(f"Eval error {node}")
            return self.coerce(op, self.eval(node.left), self.eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            if (op := self.OPERATORS.get(type(node.op))) is None:
                raise RuntimeError(f"Eval error {node}")
            return op(self.eval(node.operand))
        elif isinstance(node, ast.Assign):
            value = self.eval(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.scope_set(target.id, value)
                else:
                    raise RuntimeError(f"Eval error {node}")
            return None
        elif isinstance(node, ast.Name):
            return self.scope_get(node.id)
        elif isinstance(node, ast.Expr):
            return self.eval(node.value)
        elif isinstance(node, ast.IfExp):
            if self.eval(node.test):
                return self.eval(node.body)
            else:
                return self.eval(node.orelse)
        elif isinstance(node, ast.ListComp):
            if len(node.generators) != 1:
                raise RuntimeError(f"Eval error {node}")

            comp = node.generators[0]
            assert isinstance(comp, ast.comprehension)
            name = comp.target
            assert isinstance(name, ast.Name)
            name = name.id
            seq = self.eval(comp.iter)

            self.scope_push()

            lst = []
            for elem in seq:
                self.scope_set(name, elem)

                if not all(self.eval(cond) for cond in comp.ifs):
                    continue

                lst.append(self.eval(node.elt))

            self.scope_pop()

            return lst
        elif isinstance(node, ast.Call):
            assert len(node.keywords) == 0
            func = self.eval(node.func)
            return func(*[self.eval(val) for val in node.args])
        elif isinstance(node, ast.List):
            return [self.eval(val) for val in node.elts]
        elif isinstance(node, ast.Subscript):
            return self.eval(node.value).__getitem__(self.eval(node.slice))
        elif isinstance(node, ast.Slice):
            return slice(self.eval(node.lower), self.eval(node.upper), self.eval(node.step))
        elif isinstance(node, ast.Attribute):
            val = self.eval(node.value)
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

                self.return_stack.append(None)

                self.scope_push()
                for i, arg in enumerate(node.args.args):
                    self.scope_set(arg.arg, args[i])

                self.eval(node.body)

                self.scope_pop()

                return self.return_stack.pop(-1)

            self.scope_set(node.name, func)
        elif isinstance(node, ast.Return):
            self.return_stack[-1] = self.eval(node.value)
        else:
            raise RuntimeError(f"Eval error {node}")
