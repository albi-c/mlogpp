import enum

from .error import MlogError


class Type(enum.Flag):
    NUM = enum.auto()
    STR = enum.auto()
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


class Value:
    writable: bool
    type: Type

    def __init__(self, writable: bool, type_: Type):
        self.writable = writable
        self.type = type_

    def __str__(self):
        raise MlogError(f"Invalid value [{repr(self)}]")

    def __hash__(self):
        return hash((self.writable, self.type))


class StringValue(Value):
    value: str

    def __init__(self, value: str):
        super().__init__(False, Type.STR)

        self.value = value

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash((self.writable, self.type, self.value))


class NumberValue(Value):
    value: int | float

    def __init__(self, value: int | float):
        super().__init__(False, Type.NUM)

        self.value = value

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash((self.writable, self.type, self.value))


class NullValue(Value):
    value: None

    def __init__(self):
        super().__init__(False, Type.NULL)

        self.value = None

    def __str__(self):
        return "null"

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash((self.writable, self.type, self.value))


class VariableValue(Value):
    name: str

    def __init__(self, type_: Type, name: str, writable: bool = True):
        super().__init__(writable, type_)

        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.type == other.type and self.name == other.name and self.writable == other.writable

    def __hash__(self):
        return hash((self.writable, self.type, self.name))
