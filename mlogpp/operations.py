import typing

from .instruction import InstructionOp
from .generator import Gen
from .values import Type, Value, VariableValue, SettableValue, NumberValue
from .error import Error


class Operations:
    UNARY: dict[str, typing.Callable[[str, str], list[str | int]]] = {
        "-": lambda result, value: ["sub", result, 0, value],
        "~": lambda result, value: ["flip", result, value, 0],
        "!": lambda result, value: ["not", result, value, 0]
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

    @classmethod
    def unary(cls, op: str, value: Value) -> Value | None | typing.Callable:
        if op in cls.UNARY:
            if isinstance(value, NumberValue):
                try:
                    result = float(cls.UNARY_PRECALC[op](value.value))
                    if result.is_integer():
                        result = int(result)
                    return NumberValue(result)
                except (TypeError, ArithmeticError, KeyError):
                    pass

            if value.type() not in Type.NUM:
                return lambda node: Error.incompatible_types(node, value.type(), Type.NUM)

            result = Gen.tmp()
            Gen.emit(
                InstructionOp(*cls.UNARY[op](result, value.get()))
            )
            return VariableValue(result, Type.NUM)

        return None

    @classmethod
    def binary(cls, a: Value, op: str, b: Value) -> Value | None | typing.Callable:
        if op == "=":
            if isinstance(a, SettableValue) and not a.const():
                a.set(b)
                return b

            else:
                return lambda node: Error.write_to_const(node, str(a))

        elif op in cls.ASSIGNMENT:
            if a.type() not in Type.NUM:
                return lambda node: Error.incompatible_types(node, a.type(), Type.NUM)

            if b.type() not in Type.NUM:
                return lambda node: Error.incompatible_types(node, b.type(), Type.NUM)

            if isinstance(a, SettableValue) and not a.const():
                result = Gen.tmp()
                Gen.emit(
                    InstructionOp(cls.ASSIGNMENT[op], result, a.get(), b.get())
                )
                a.set(VariableValue(result, Type.NUM))
                return a

            else:
                return lambda node: Error.write_to_const(node, str(a))

        elif op in cls.BINARY:
            if isinstance(a, NumberValue) and isinstance(b, NumberValue):
                try:
                    result = float(cls.BINARY_PRECALC[op](a.value, b.value))
                    if result.is_integer():
                        result = int(result)
                    return NumberValue(result)
                except (TypeError, ArithmeticError, KeyError):
                    pass

            if op not in cls.EQUALITY:
                if a.type() not in Type.NUM:
                    return lambda node: Error.incompatible_types(node, a.type(), Type.NUM)

                if b.type() not in Type.NUM:
                    return lambda node: Error.incompatible_types(node, b.type(), Type.NUM)

            result = Gen.tmp()
            Gen.emit(
                InstructionOp(cls.BINARY[op], result, a.get(), b.get())
            )
            return VariableValue(result, Type.NUM)

        return None
