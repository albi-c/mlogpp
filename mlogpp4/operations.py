import typing

from .instruction import InstructionOp
from .generator import Gen
from .values import Type, Value, VariableValue, SettableValue
from .error import Error


class Operations:
    @classmethod
    def unary(cls, op: str, value: Value) -> Value | None | typing.Callable:
        return None

    @classmethod
    def binary(cls, a: Value, op: str, b: Value) -> Value | None | typing.Callable:
        if op == "*":
            result = Gen.tmp()
            Gen.emit(
                InstructionOp("mul", result, a.get(), b.get())
            )
            return VariableValue(result, Type.NUM)

        elif op == "=":
            if isinstance(a, SettableValue) and not a.const():
                a.set(b)
                return b

            else:
                return lambda node: Error.write_to_const(node, str(a))

        elif op == "===":
            result = Gen.tmp()
            Gen.emit(
                InstructionOp("strictEqual", result, a.get(), b.get())
            )
            return VariableValue(result, Type.NUM)

        # TODO: all operators, [!, ~, ...], [/, -, ...], [/=, -=, ...]

        return None
