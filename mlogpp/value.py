from __future__ import annotations

import enum

from .error import Error


class Type(enum.Flag):
    """
    Type of value.
    """

    STR = enum.auto()
    NUM = enum.auto()
    NULL = enum.auto()

    BLOCK = enum.auto()
    UNIT = enum.auto()
    TEAM = enum.auto()

    UNIT_TYPE = enum.auto()
    ITEM_TYPE = enum.auto()
    BLOCK_TYPE = enum.auto()
    LIQUID_TYPE = enum.auto()

    CONTROLLER = enum.auto()

    ANY = NUM | STR | NULL | BLOCK | UNIT | TEAM | UNIT_TYPE | ITEM_TYPE | BLOCK_TYPE | LIQUID_TYPE | CONTROLLER

    @staticmethod
    def from_code(var: str) -> 'Type':
        """
        Create a type from an in-code name without "_"

        Args:
            var: The in-code name.

        Returns:
            The created type.
        """

        tok = ""
        last = ""
        for ch in var:
            if ch.upper() == ch and last:
                tok += "_"
            tok += ch
            last = ch

        return Type[tok.upper()]


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
            return StringValue(f"\"{val}\"")
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
