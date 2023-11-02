from __future__ import annotations

import typing
from dataclasses import dataclass

from .error import Error


@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class Type:
    types: set[str]
    any_: bool
    convertible_from: set[str]
    convertible_to: set[str]

    typenames = {}
    any_type = None

    # builtin types
    NUM = None
    STR = None
    NULL = None
    BLOCK = None
    UNIT = None
    TEAM = None
    UNIT_TYPE = None
    ITEM_TYPE = None
    BLOCK_TYPE = None
    LIQUID_TYPE = None
    CONTROLLER = None
    COLOR = None

    # private types
    OBJECT = None

    # compound types
    CONTENT = None
    ANY = None

    reset_typenames = {}

    @classmethod
    def register(cls, name: str, type_: Type):
        cls.typenames[name] = type_

    @classmethod
    def reset_set(cls):
        cls.reset_typenames = cls.typenames.copy()

    @classmethod
    def reset(cls):
        cls.typenames = cls.reset_typenames.copy()

    @classmethod
    def simple(cls, name: str) -> Type:
        if name in cls.typenames:
            return cls.typenames[name]

        type_ = cls({name}, False, set(), set())
        cls.typenames[name] = type_
        return type_

    @classmethod
    def private(cls, name: str) -> Type:
        return cls.simple(f"${name}")

    def is_private(self) -> bool:
        return any(t.startswith("$") for t in self.types) or self.any_

    @classmethod
    def function(cls, params: list[Type], ret: Type | list[Type]) -> Type:
        if isinstance(ret, list):
            return cls.simple(f"({','.join(map(str, params))} -> {','.join(map(str, ret))})")

        else:
            return cls.simple(f"({','.join(map(str, params))} -> {ret})")

    @classmethod
    def any(cls):
        if cls.any_type is None:
            cls.any_type = cls(set(), True, set(), set())

        return cls.any_type

    @classmethod
    def parse(cls, name: str, node) -> Type:
        if name in cls.typenames:
            return cls.typenames[name]

        Error.undefined_type(node, name)

    def list_types(self) -> typing.Iterable[Type]:
        for name in self.types:
            yield Type({name}, False, set(), set())

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

            return other.types & self.types == other.types or other.types == {"null"} \
                   or other.types & self.convertible_from == other.types or self.types & other.convertible_to == self.types

        return False

    def __or__(self, other):
        if isinstance(other, Type):
            return Type(self.types | other.types, self.any_ or other.any_,
                        self.convertible_from & other.convertible_from, self.convertible_to & other.convertible_to)

        return NotImplemented

    def __ior__(self, _):
        raise RuntimeError


# builtin types
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

Type.COLOR = Type.simple("Color")
Type.COLOR.convertible_from.add("num")

# private types
Type.OBJECT = Type.private("object")

# compound types
Type.CONTENT = Type.UNIT_TYPE | Type.ITEM_TYPE | Type.BLOCK_TYPE | Type.LIQUID_TYPE
Type.register("Content", Type.CONTENT)

Type.ANY = Type.any()

Type.reset_set()
