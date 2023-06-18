from .instruction import InstructionOp
from .generator import Gen
from .values import Type, Value, VariableValue


class Operations:
    @classmethod
    def unary(cls, op: str, value: Value) -> Value | None:
        return None

    @classmethod
    def binary(cls, a: Value, op: str, b: Value) -> Value | None:
        if op == "*":
            result = Gen.tmp()
            Gen.emit(
                InstructionOp("mul", result, a.get(), b.get())
            )
            return VariableValue(result, Type.NUM)

        # TODO: all operators

        return None
