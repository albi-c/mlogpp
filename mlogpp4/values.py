from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from .error import Error
from .generator import Gen
from .instruction import InstructionSet


@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class Type:
    types: set[str]

    typenames = {}

    @classmethod
    def simple(cls, name: str) -> Type:
        if name in cls.typenames:
            return cls.typenames[name]

        type_ = cls({name})
        cls.typenames[name] = type_
        return type_

    @classmethod
    def function(cls, params: list[Type], ret: Type) -> Type:
        return cls.simple(f"({','.join(map(str, params))} -> {ret})")

    @classmethod
    def parse(cls, name: str, node: 'Node') -> Type:
        if name in cls.typenames:
            return cls.typenames[name]

        Error.undefined_type(node, name)

    def __class_getitem__(cls, name: str) -> Type:
        return cls.typenames[name]

    def __str__(self):
        return f"[{' | '.join(self.types)}]"

    def __eq__(self, other):
        if isinstance(other, Type):
            return self.types == other.types

        return False

    def __hash__(self):
        return hash(tuple(self.types))

    def __contains__(self, other):
        if isinstance(other, Type):
            return other.types & self.types == other.types

        return False

    def __or__(self, other):
        if isinstance(other, Type):
            return Type(self.types | other.types)

        return NotImplemented

    def __ior__(self, _):
        raise RuntimeError


Type.NUM = Type.simple("num")
Type.STR = Type.simple("str")
Type.NULL = Type.simple("null")

Type.BLOCK = Type.simple("Block")
Type.UNIT = Type.simple("Unit")
Type.TEAM = Type.simple("Team")

Type.UNIT_TYPE = Type.simple("UnitType")
Type.ITEM_TYPE = Type.simple("ItemType")
Type.BLOCK_TYPE = Type.simple("BlockType")
Type.LIQUID_TYPE = Type.simple("LiquidType")

Type.CONTROLLER = Type.simple("Controller")


class Value:
    _type: Type

    def __init__(self, type_: Type):
        self._type = type_

    def __str__(self):
        return self.get()

    def __eq__(self, other):
        raise NotImplementedError

    def get(self) -> str:
        raise NotImplementedError

    def print(self) -> tuple[str, ...]:
        return self.get(),

    def type(self) -> Type:
        return self._type

    def op_unary(self, op: str) -> Value | None:
        return None

    def op_binary(self, op: str, other: Value) -> Value | None:
        return None

    def const(self) -> bool:
        return True


class NumberValue(Value):
    value: int | float

    def __init__(self, value: int | float):
        super().__init__(Type.NUM)

        self.value = value

    def __eq__(self, other):
        if isinstance(other, NumberValue):
            return self.value == other.value

        return False

    def get(self) -> str:
        return str(self.value)


class StringValue(Value):
    value: str

    def __init__(self, value: str):
        super().__init__(Type.NUM)

        self.value = value

    def __eq__(self, other):
        if isinstance(other, StringValue):
            return self.value == other.value

        return False

    def get(self) -> str:
        return f"\"{self.value}\""


class VariableValue(Value):
    name: str
    _const: bool

    def __init__(self, name: str, type_: Type, const: bool = False):
        super().__init__(type_)

        self.name = name
        self._const = const

    def __eq__(self, other):
        if isinstance(other, VariableValue):
            return self.name == other.name and self.type() == other.type()

        return False

    def get(self) -> str:
        return self.name

    def const(self) -> bool:
        return self._const

    def op_binary(self, op: str, other: Value) -> Value | None:
        if op == "==":
            if self.type() == other.type():
                Gen.emit(
                    InstructionSet(self.name, other.get())
                )
                return self

        return None


class NullValue(Value):
    def __init__(self):
        super().__init__(Type.NULL)

    def __eq__(self, other):
        return isinstance(other, NullValue)

    def get(self) -> str:
        return "null"
