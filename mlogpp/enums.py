from .values import Type, Value, TypeImpl
from .content import Content


class EnumTypeImpl(TypeImpl):
    name: str
    type: Type
    values: dict[str, Value]

    def __init__(self, name: str, type_: Type, values: set[str], content: bool):
        self.name = name
        self.type = type_

        self.values = {}
        for value in values:
            self.values[value] = Value(self.type, ("@" if content else "") + value)

    def get(self, value: Value) -> str:
        return self.name

    def getattr(self, value: Value, name: str) -> Value | None:
        return self.values.get(name)


def make_enum(name: str, type_: Type, values: set[str], content: bool):
    return Value(type_, name, type_impl=EnumTypeImpl(name, type_, values, content))


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

EnumBlock = make_enum("BlockType", Type.BLOCK_TYPE, Content.BLOCKS, True)
EnumItem = make_enum("ItemType", Type.ITEM_TYPE, Content.ITEMS, True)
EnumLiquid = make_enum("LiquidType", Type.LIQUID_TYPE, Content.LIQUIDS, True)
EnumUnit = make_enum("UnitType", Type.UNIT_TYPE, Content.UNITS, True)
EnumTeam = make_enum("Team", Type.TEAM, Content.TEAMS, True)

EnumEffect = make_enum("Effect", Type.private("Effect"), Content.EFFECTS, False)

EnumRadarFilter = make_enum("RadarFilter", Type.private("RadarFilter"), {
    "any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground"
}, False)
EnumRadarSort = make_enum("RadarSort", Type.private("RadarSort"), {
    "distance", "health", "shield", "armor", "maxHealth"
}, False)

EnumLocateType = make_enum("LocateType", Type.private("LocateType"), {
    "core", "storage", "generator", "turret", "factory", "repair", "battery", "reactor"
}, False)


ENUMS: list[Value] = [
    EnumBlock, EnumItem, EnumLiquid, EnumUnit, EnumTeam,
    EnumEffect,
    EnumRadarFilter, EnumRadarSort,
    EnumLocateType
]

ENUM_TYPES: dict[Type, Value] = {
    enum.type: enum for enum in ENUMS
}

ENUM_TYPES_VALUES: dict[Type, dict[str, Value]] = {}
for enum in ENUMS:
    impl = enum.impl()
    if isinstance(impl, EnumTypeImpl):
        ENUM_TYPES_VALUES[impl.type] = impl.values
