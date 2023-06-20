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

    def __init__(self, name: str, type_: Type, values: set[str], content: bool):
        super().__init__(Type.OBJECT)

        self.name = name
        self.type = type_

        self.values = {}
        for value in values:
            self.values[value] = EnumValue(("@" if content else "") + value, self.type)

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
    "totalItems": Type.NUM,
    "firstItem": Type.NUM,
    "totalLiquids": Type.NUM,
    "totalPower": Type.NUM,
    "itemCapacity": Type.NUM,
    "liquidCapacity": Type.NUM,
    "powerCapacity": Type.NUM,
    "powerNetStored": Type.NUM,
    "powerNetCapacity": Type.NUM,
    "powerNetIn": Type.NUM,
    "powerNetOut": Type.NUM,
    "ammo": Type.NUM,
    "ammoCapacity": Type.NUM,
    "health": Type.NUM,
    "maxHealth": Type.NUM,
    "heat": Type.NUM,
    "efficiency": Type.NUM,
    "progress": Type.NUM,
    "timescale": Type.NUM,
    "rotation": Type.NUM,
    "x": Type.NUM,
    "y": Type.NUM,
    "shootX": Type.NUM,
    "shootY": Type.NUM,
    "size": Type.NUM,
    "dead": Type.NUM,
    "range": Type.NUM,
    "shooting": Type.NUM,
    "boosting": Type.NUM,
    "mineX": Type.NUM,
    "mineY": Type.NUM,
    "mining": Type.NUM,
    "speed": Type.NUM,
    "team": Type.NUM,
    "type": Type.NUM,
    "flag": Type.NUM,
    "controlled": Type.CONTROLLER,
    "controller": Type.BLOCK | Type.UNIT,
    "name": Type.NUM,
    "payloadCount": Type.NUM,
    "payloadType": Type.NUM,
    "enabled": Type.NUM,
    "config": Type.NUM,
    "color": Type.NUM
} | {
    item: Type.NUM for item in Content.ITEMS
} | {
    liquid: Type.NUM for liquid in Content.LIQUIDS
}

SETPROP: dict[str, Type] = {
    "x": Type.NUM,
    "y": Type.NUM,
    "rotation": Type.NUM,
    "team": Type.TEAM,
    "flag": Type.NUM,
    "health": Type.NUM,
    "totalPower": Type.NUM,
    "payloadType": Type.NUM
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

# (num) if False, else (num, Team)
RULES: dict[str, bool] = {
    rule: False for rule in [
        "currentWaveTimer", "waveTimer", "waves", "wave", "waveSpacing", "waveSending", "attackMode",
        "enemyCoreBuildRadius", "dropZoneRadius", "unitCap", "lighting", "ambientLight", "solarMultiplier"
    ]
} | {
    rule: True for rule in [
        "buildSpeed", "unitHealth", "unitBuildSpeed", "unitCost", "unitDamage", "blockHealth", "blockDamage",
        "rtsMinWeight", "rtsMinSquad"
    ]
}

Content.SENSABLE = SENSABLE
Content.CONTROLLABLE = CONTROLLABLE

EnumBlock = Enum("BlockType", Type.BLOCK_TYPE, Content.BLOCKS, True)
EnumItem = Enum("ItemType", Type.ITEM_TYPE, Content.ITEMS, True)
EnumLiquid = Enum("LiquidType", Type.LIQUID_TYPE, Content.LIQUIDS, True)
EnumUnit = Enum("UnitType", Type.UNIT_TYPE, Content.UNITS, True)
EnumTeam = Enum("Team", Type.TEAM, Content.TEAMS, True)

EnumEffect = Enum("Effect", Type.private("Effect"), Content.EFFECTS, False)

EnumRadarFilter = Enum("RadarFilter", Type.private("RadarFilter"), {
    "any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground"
}, False)
EnumRadarSort = Enum("RadarSort", Type.private("RadarSort"), {
    "distance", "health", "shield", "armor", "maxHealth"
}, False)

EnumLocateType = Enum("LocateType", Type.private("LocateType"), {
    "core", "storage", "generator", "turret", "factory", "repair", "battery", "reactor"
}, False)


ENUMS: list[Enum] = [
    EnumBlock, EnumItem, EnumLiquid, EnumUnit, EnumTeam,
    EnumEffect,
    EnumRadarFilter, EnumRadarSort,
    EnumLocateType
]

ENUM_TYPES: dict[Type, Enum] = {
    enum.type: enum for enum in ENUMS
}
