from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from .error import Error
from .generator import Gen
from .instruction import InstructionSet, InstructionRead, InstructionWrite, InstructionJump, InstructionOp
from .abi import ABI


@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class Type:
    types: set[str]
    any_: bool

    typenames = {}
    any_type = None

    @classmethod
    def simple(cls, name: str) -> Type:
        if name in cls.typenames:
            return cls.typenames[name]

        type_ = cls({name}, False)
        cls.typenames[name] = type_
        return type_

    @classmethod
    def function(cls, params: list[Type], ret: Type) -> Type:
        return cls.simple(f"({','.join(map(str, params))} -> {ret})")

    @classmethod
    def any(cls):
        if cls.any_type is None:
            cls.any_type = cls(set(), True)

        return cls.any_type

    @classmethod
    def parse(cls, name: str, node: 'Node') -> Type:
        if name in cls.typenames:
            return cls.typenames[name]

        Error.undefined_type(node, name)

    def __class_getitem__(cls, name: str) -> Type:
        return cls.typenames[name]

    def __str__(self):
        if self.any_:
            return "[any]"

        return f"[{' | '.join(self.types)}]"

    def __eq__(self, other):
        if isinstance(other, Type):
            if self.any_:
                return other.any_

            return self.types == other.types

        return False

    def __hash__(self):
        if self.any_:
            return hash("AnyType")

        return hash(tuple(self.types))

    def __contains__(self, other):
        if isinstance(other, Type):
            if self.any_:
                return True

            if other.any_:
                return self.any_

            return other.types & self.types == other.types

        return False

    def __or__(self, other):
        if isinstance(other, Type):
            if other.any_:
                return Type(set(), True)

            return Type(self.types | other.types, False)

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

Type.ANY = Type.any()


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

    # TODO: into(var) optimization

    def print(self) -> tuple[str, ...]:
        return self.get(),

    def type(self) -> Type:
        return self._type

    def const(self) -> bool:
        return True


class SettableValue(Value, ABC):
    def set(self, value: Value):
        raise NotImplementedError


class CallableValue(Value, ABC):
    def call(self, node: 'Node', params: list[Value]) -> Value:
        raise NotImplementedError


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
        super().__init__(Type.STR)

        self.value = value

    def __eq__(self, other):
        if isinstance(other, StringValue):
            return self.value == other.value

        return False

    def get(self) -> str:
        return self.value


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


class NullValue(Value):
    def __init__(self):
        super().__init__(Type.NULL)

    def __eq__(self, other):
        return isinstance(other, NullValue)

    def get(self) -> str:
        return "null"


class IndexedValue(SettableValue):
    cell: str
    index: str

    def __init__(self, cell: str, index: str):
        super().__init__(Type.NUM)

        self.cell = cell
        self.index = index

    def __eq__(self, other):
        if isinstance(other, IndexedValue):
            return self.cell == other.cell and self.index == other.index

        return False

    def get(self) -> str:
        var = Gen.tmp()
        Gen.emit(
            InstructionRead(var, self.cell, self.index)
        )

        return var

    def set(self, value: Value):
        val = value.get()
        Gen.emit(
            InstructionWrite(val, self.cell, self.index)
        )


class FunctionValue(CallableValue):
    name: str
    params: list[tuple[Type, str]]
    ret: Type

    def __init__(self, name: str, params: list[tuple[Type, str]], ret: Type):
        super().__init__(Type.function([param[0] for param in params], ret))

        self.name = name
        self.params = params
        self.ret = ret

    def __eq__(self, other):
        if isinstance(other, FunctionValue):
            return self.name == other.name and self.type() == other.type()

        return False

    def get(self) -> str:
        return str(self.type())

    def call(self, node: 'Node', params: list[Value]) -> Value:
        for i, [type_, name] in enumerate(self.params):
            if params[i].type() not in type_:
                Error.incompatible_types(node, params[i].type(), type_)

            Gen.emit(
                InstructionSet(name, params[i].get())
            )

        Gen.emit(
            InstructionOp("add", ABI.function_return_pos(self.name), "@counter", 1),
            InstructionJump(self.name, "always", 0, 0)
        )

        return VariableValue(ABI.function_return(self.name), self.ret)
