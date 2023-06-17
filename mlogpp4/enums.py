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


class Enum:
    name: str
    type: Type
    values: set[str]

    def __init__(self, name: str, type_: Type, values: set[str]):
        self.name = name
        self.type = type_
        self.values = values

    def __getitem__(self, value: str) -> EnumValue:
        if value in self.values:
            return EnumValue(value, self.type)

        raise NameError("invalid enum item")


EnumUnitType = Enum("UnitType", Type.UNIT_TYPE, {
    "nova"
})
