import typing
import math

from .instruction import InstructionOp
from .generator import Gen
from .values import Type, Value
from .error import Error


class Operations:
    UNARY: dict[str, typing.Callable[[str, str], list[str | int]]] = {
        "-": lambda result, value: ["sub", result, 0, value],
        "~": lambda result, value: ["flip", result, value, 0],
        "!": lambda result, value: ["equal", result, value, 0]
    }

    BINARY: dict[str, str] = {
        "+": "add",
        "-": "sub",
        "*": "mul",
        "/": "div",
        "//": "idiv",
        "%": "mod",
        "**": "pow",
        "==": "equal",
        "!=": "notEqual",
        "&&": "land",
        "||": "or",
        "<": "lessThan",
        "<=": "lessThanEq",
        ">": "greaterThan",
        ">=": "greaterThanEq",
        "===": "strictEqual",
        "<<": "shl",
        ">>": "shr",
        "|": "or",
        "&": "and",
        "^": "xor"
    }

    EQUALITY: set[str] = {
        "==",
        "!=",
        "==="
    }

    ASSIGNMENT: dict[str, str] = {
        "+=": "add",
        "-=": "sub",
        "%=": "mod",
        "&=": "and",
        "|=": "or",
        "^=": "xor",
        "*=": "mul",
        "/=": "div",
        "**=": "pow",
        "//=": "idiv",
        "<<=": "shl",
        ">>=": "shr"
    }

    UNARY_PRECALC: dict[str, typing.Callable[[int | float], int | float]] = {
        "-": lambda x: -x,
        "~": lambda x: ~x,
        "!": lambda x: not x
    }

    BINARY_PRECALC: dict[str, typing.Callable[[int | float, int | float], int | float]] = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a / b,
        "//": lambda a, b: a // b,
        "%": lambda a, b: a % b,
        "**": lambda a, b: a ** b,
        "&&": lambda a, b: a and b,
        "||": lambda a, b: a or b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "===": lambda a, b: a == b,
        "<<": lambda a, b: a << b,
        ">>": lambda a, b: a >> b,
        "|": lambda a, b: a | b,
        "&": lambda a, b: a & b,
        "^": lambda a, b: a ^ b
    }

    PRECALC: dict[str, typing.Callable[[int | float, int | float | None], int | float]] = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b,
        "idiv": lambda a, b: a // b,
        "mod": lambda a, b: a % b,
        "pow": lambda a, b: a ** b,
        "not": lambda a, _: not a,
        "land": lambda a, b: a and b,
        "lessThan": lambda a, b: a < b,
        "lessThanEq": lambda a, b: a <= b,
        "greaterThan": lambda a, b: a > b,
        "greaterThanEq": lambda a, b: a >= b,
        "strictEqual": lambda a, b: a == b,
        "shl": lambda a, b: a << b,
        "shr": lambda a, b: a >> b,
        "or": lambda a, b: a | b,
        "and": lambda a, b: a & b,
        "xor": lambda a, b: a ^ b,
        "flip": lambda a, _: ~a,
        "max": lambda a, b: max(a, b),
        "min": lambda a, b: min(a, b),
        "abs": lambda a, _: abs(a),
        "log": lambda a, _: math.log(a),
        "log10": lambda a, _: math.log10(a),
        "floor": lambda a, _: math.floor(a),
        "ceil": lambda a, _: math.ceil(a),
        "sqrt": lambda a, _: math.sqrt(a),
        "angle": lambda a, b: math.atan2(b, a) * 180 / math.pi,
        "length": lambda a, b: math.sqrt(a * a + b * b),
        "sin": lambda a, _: math.sin(math.radians(a)),
        "cos": lambda a, _: math.cos(math.radians(a)),
        "tan": lambda a, _: math.tan(math.radians(a)),
        "asin": lambda a, _: math.degrees(math.asin(a)),
        "acos": lambda a, _: math.degrees(math.acos(a)),
        "atan": lambda a, _: math.degrees(math.atan(a))

        # noise and rand not implemented
        # equal and notEqual are not implemented because they use type conversion
    }

    JUMP_PRECALC: dict[str, typing.Callable[[int | float, int | float | None], int | float]] = {
        "lessThan": lambda a, b: a < b,
        "lessThanEq": lambda a, b: a <= b,
        "greaterThan": lambda a, b: a > b,
        "greaterThanEq": lambda a, b: a >= b,
        "strictEqual": lambda a, b: a == b
    }

    @classmethod
    def unary(cls, op: str, value: Value) -> Value | None | typing.Callable:
        if op in cls.UNARY:
            if value.type() not in Type.NUM:
                return lambda node: Error.incompatible_types(node, value.type(), Type.NUM)

            try:
                val = float(value.value)
                if val.is_integer():
                    val = int(val)
                result = float(cls.UNARY_PRECALC[op](val))
                if result.is_integer():
                    result = int(result)
                return Value.number(result)
            except (TypeError, ArithmeticError, KeyError, ValueError):
                pass

            result = Gen.tmp()
            Gen.emit(
                InstructionOp(*cls.UNARY[op](result, value.get()))
            )
            return Value.variable(result, Type.NUM)

        return None

    @classmethod
    def binary(cls, a: Value, op: str, b: Value) -> Value | None | typing.Callable:
        if op == "=":
            if not a.const():
                if b.type_get() not in a.type_set():
                    conv = b.get_as(a.type_set())
                    if conv is not None:
                        a.set(conv)
                        return conv

                    return lambda node: Error.incompatible_types(node, b.type(), a.type())

                a.set(b)
                return b

            else:
                return lambda node: Error.write_to_const(node, a.get())

        elif op in cls.ASSIGNMENT:
            if a.type() not in Type.NUM:
                return lambda node: Error.incompatible_types(node, a.type(), Type.NUM)

            if b.type() not in Type.NUM:
                return lambda node: Error.incompatible_types(node, b.type(), Type.NUM)

            if not a.const():
                result = Gen.tmp()
                Gen.emit(
                    InstructionOp(cls.ASSIGNMENT[op], result, a.get(), b.get())
                )
                a.set(Value.variable(result, Type.NUM))
                return a

            else:
                return lambda node: Error.write_to_const(node, str(a))

        elif op in cls.BINARY:
            if op not in cls.EQUALITY:
                if a.type() not in Type.NUM:
                    return lambda node: Error.incompatible_types(node, a.type(), Type.NUM)

                if b.type() not in Type.NUM:
                    return lambda node: Error.incompatible_types(node, b.type(), Type.NUM)

                try:
                    x = float(a.value)
                    if x.is_integer():
                        x = int(x)
                    y = float(b.value)
                    if y.is_integer():
                        y = int(y)
                    result = float(cls.BINARY_PRECALC[op](x, y))
                    if result.is_integer():
                        result = int(result)
                    return Value.number(result)
                except (TypeError, ArithmeticError, KeyError, ValueError):
                    pass

            result = Gen.tmp()
            Gen.emit(
                InstructionOp(cls.BINARY[op], result, a.get(), b.get())
            )
            return Value.variable(result, Type.NUM)

        return None
