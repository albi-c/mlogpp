from .values import Type, Value
from .content import Content


class EnumValue(Value):
    value: str

    def __init__(self, value: str, type_: Type):
        super().__init__(type_)

        self.value = value

    def __eq__(self, other):
        if isinstance(other, EnumValue):
            return self.value == other.value and self.type() == other.type()

        return False

    def get(self) -> str:
        return self.value


class Enum(Value):
    name: str
    type: Type
    values: dict[str, EnumValue]

    def __init__(self, name: str, type_: Type, values: set[str]):
        super().__init__(Type.OBJECT)

        self.name = name
        self.type = type_

        self.values = {}
        for value in values:
            self.values[value] = EnumValue(value, self.type)

    def __eq__(self, other):
        if isinstance(other, Enum):
            return self.name == other.name and self.type == other.type and self.values == other.values

        return False

    def __hash__(self):
        return hash((self.name, self.type))

    def get(self) -> str:
        return self.name

    def getattr(self, name: str) -> Value | None:
        return self.values.get(name)


SENSABLE: dict[str, Type] = {
    # TODO: fill in
} | {
    item: Type.NUM for item in Content.ITEMS
} | {
    liquid: Type.NUM for liquid in Content.LIQUIDS
}

CONTROLLABLE: dict[str, Type] = {
    "enabled": Type.NUM,
    "config": Type.CONTENT,
    "color": Type.NUM
}

Content.SENSABLE = SENSABLE
Content.CONTROLLABLE = CONTROLLABLE

EnumBlock = Enum("BlockType", Type.BLOCK_TYPE, Content.BLOCKS)
EnumItem = Enum("ItemType", Type.ITEM_TYPE, Content.ITEMS)
EnumLiquid = Enum("LiquidType", Type.LIQUID_TYPE, Content.LIQUIDS)
EnumUnit = Enum("UnitType", Type.UNIT_TYPE, Content.UNITS)

EnumEffect = Enum("Effect", Type.private("Effect"), Content.EFFECTS)

EnumRadarFilter = Enum("RadarFilter", Type.private("RadarFilter"), {
    "any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground"
})
EnumRadarSort = Enum("RadarSort", Type.private("RadarSort"), {
    "distance", "health", "shield", "armor", "maxHealth"
})

EnumLocateType = Enum("LocateType", Type.private("LocateType"), {
    "core", "storage", "generator", "turret", "factory", "repair", "battery", "reactor"
})


ENUMS: list[Enum] = [
    EnumBlock, EnumItem, EnumLiquid, EnumUnit,
    EnumEffect,
    EnumRadarFilter, EnumRadarSort,
    EnumLocateType
]

ENUM_TYPES: dict[Type, Enum] = {
    enum.type: enum for enum in ENUMS
}
