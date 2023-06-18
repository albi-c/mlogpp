from .values import Type, Value


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
    values: set[str]

    def __init__(self, name: str, type_: Type, values: set[str]):
        super().__init__(type_)

        self.name = name
        self.type = type_
        self.values = values

    def __eq__(self, other):
        if isinstance(other, Enum):
            return self.name == other.name and self.type == other.type and self.values == other.values

        return False

    def get(self) -> str:
        return self.name

    def getattr(self, name: str) -> Value | None:
        if name in self.values:
            return EnumValue(name, self.type)

        return None


# TODO: content enums

EnumSensable = Enum("Sensable", Type.private("Sensable"), {
    "$placeholder"
    # TODO: fill in
})

EnumRadarFilter = Enum("RadarFilter", Type.private("RadarFilter"), {
    "any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground"
})
EnumRadarSort = Enum("RadarSort", Type.private("RadarSort"), {
    "distance", "health", "shield", "armor", "maxHealth"
})
