from __future__ import annotations

import enum

from .error import Error


class Type:
    """
    Type of value.
    """

    names: set[str]

    @staticmethod
    def new(name: str):
        return Type({name})

    def __init__(self, names: set[str]):
        self.names = names

    def __contains__(self, item):
        if isinstance(item, Type):
            return self.names & item.names == item.names

        raise TypeError

    def __or__(self, other):
        if isinstance(other, Type):
            return Type(self.names | other.names)

        raise TypeError

    def __and__(self, other):
        if isinstance(other, Type):
            return Type(self.names & other.names)

        raise TypeError


Type.STR = Type.new("str")
Type.NUM = Type.new("num")
Type.NULL = Type.new("null")

Type.BLOCK = Type.new("Block")
Type.UNIT = Type.new("Unit")
Type.TEAM = Type.new("Team")

Type.UNIT_TYPE = Type.new("UnitType")
Type.ITEM_TYPE = Type.new("ItemType")
Type.BLOCK_TYPE = Type.new("BlockType")
Type.LIQUID_TYPE = Type.new("LiquidType")

Type.CONTROLLER = Type.new("Controller")

Type.ANY = Type.NUM | Type.STR | Type.NULL | Type.BLOCK | Type.UNIT | Type.TEAM | Type.UNIT_TYPE | \
           Type.ITEM_TYPE | Type.BLOCK_TYPE | Type.LIQUID_TYPE | Type.CONTROLLER


class Value:
    type: Type

    def __init__(self, type_: Type):
        self.type = type_

    def __str__(self):
        raise Error(f"Invalid value [{repr(self)}]")

    def __hash__(self):
        return hash(self.type)

    @staticmethod
    def from_(val) -> Value:
        if isinstance(val, str):
            return StringValue(val)
        elif isinstance(val, int | float):
            return NumberValue(val)
        return NullValue()


class StringValue(Value):
    value: str

    __match_args__ = ("value",)

    def __init__(self, value: str):
        super().__init__(Type.STR)

        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"StringValue(\"{self.value}\")"

    def __hash__(self):
        return hash((self.type, self.value))


class NumberValue(Value):
    value: int | float

    __match_args__ = ("value",)

    def __init__(self, value: int | float):
        super().__init__(Type.NUM)

        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"NumberValue({self.value})"

    def __hash__(self):
        return hash((self.type, self.value))


class NullValue(Value):
    value: None

    __match_args__ = tuple()

    def __init__(self):
        super().__init__(Type.NULL)

        self.value = None

    def __str__(self):
        return "null"

    def __repr__(self):
        return f"NullValue()"

    def __hash__(self):
        return hash((self.type, self.value))


class BlockValue(Value):
    name: str

    __match_args__ = ("name",)

    def __init__(self, name: str):
        super().__init__(Type.BLOCK)

        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"BlockValue({self.value})"

    def __hash__(self):
        return hash((self.type, self.name))


class VariableValue(Value):
    name: str
    const: bool
    const_val: Value

    __match_args__ = ("name", "type", "const")

    def __init__(self, type_: Type, name: str, const: bool = False, const_val: Value = None):
        super().__init__(type_)

        self.name = name
        self.const = const
        self.const_val = const_val

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"VariableValue({self.name}{' | const' if self.const else ''})"

    def __hash__(self):
        return hash((self.type, self.name, self.const))
