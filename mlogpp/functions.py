import math
import enum

from .value import Type
from . import constants


class Param(enum.Enum):
    """
    Parameter type to a native function.
    """

    INPUT = enum.auto()
    OUTPUT = enum.auto()
    CONFIG = enum.auto()
    UNUSED = enum.auto()


class Natives:
    # native functions
    NATIVES = {
                  "read": (
                      (Param.OUTPUT, Type.NUM),
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM)
                  ),

                  "write": (
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM)
                  ),

                  "draw.clear": (
                                    (Param.INPUT, Type.NUM),
                                ) * 3,
                  "draw.color": (
                                    (Param.INPUT, Type.NUM),
                                ) * 4,
                  "draw.col": (
                      (Param.INPUT, Type.NUM),
                  ),
                  "draw.stroke": (
                      (Param.INPUT, Type.NUM),
                  ),
                  "draw.line": (
                                   (Param.INPUT, Type.NUM),
                               ) * 4,
                  "draw.rect": (
                                   (Param.INPUT, Type.NUM),
                               ) * 4,
                  "draw.lineRect": (
                                       (Param.INPUT, Type.NUM),
                                   ) * 4,
                  "draw.poly": (
                                   (Param.INPUT, Type.NUM),
                               ) * 5,
                  "draw.linePoly": (
                                       (Param.INPUT, Type.NUM),
                                   ) * 5,
                  "draw.triangle": (
                                       (Param.INPUT, Type.NUM),
                                   ) * 5,
                  "draw.image": (
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.ITEM_TYPE),
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM)
                  ),

                  "print": (
                      (Param.INPUT, Type.ANY),
                  ),

                  "drawflush": (
                      (Param.INPUT, Type.BLOCK),
                  ),

                  "printflush": (
                      (Param.INPUT, Type.BLOCK),
                  ),

                  "getlink": (
                      (Param.OUTPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM)
                  ),

                  "control.enabled": (
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM)
                  ),
                  "control.shoot": (
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM)
                  ),
                  "control.shootp": (
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.UNIT),
                      (Param.INPUT, Type.NUM)
                  ),
                  "control.config": (
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM)
                  ),
                  "control.color": (
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM)
                  ),

                  "radar": (
                      (Param.CONFIG, ("any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground")),
                      (Param.CONFIG, ("any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground")),
                      (Param.CONFIG, ("any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground")),
                      (Param.CONFIG, ("distance", "health", "shield", "armor", "maxHealth")),
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM),
                      (Param.OUTPUT, Type.UNIT)
                  )
              } | \
              {
                  f"sensor.{property}": (
                      (Param.OUTPUT, type_),
                      (Param.INPUT, Type.BLOCK | Type.UNIT)
                  ) for property, type_ in constants.SENSOR_READABLE.items()
              } | \
              {
                  "wait": (
                      (Param.INPUT, Type.NUM),
                  ),

                  "lookup.block": (
                      (Param.OUTPUT, Type.BLOCK_TYPE),
                      (Param.INPUT, Type.NUM)
                  ),
                  "lookup.unit": (
                      (Param.OUTPUT, Type.UNIT_TYPE),
                      (Param.INPUT, Type.NUM)
                  ),
                  "lookup.item": (
                      (Param.OUTPUT, Type.ITEM_TYPE),
                      (Param.INPUT, Type.NUM)
                  ),
                  "lookup.liquid": (
                      (Param.OUTPUT, Type.LIQUID_TYPE),
                      (Param.INPUT, Type.NUM)
                  ),

                  "packcolor": (
                                   (Param.OUTPUT, Type.NUM),
                               ) + (
                                   (Param.INPUT, Type.NUM),
                               ) * 4,

                  "ubind": (
                      (Param.INPUT, Type.UNIT_TYPE),
                  ),

                  "ucontrol.idle": tuple(),
                  "ucontrol.stop": tuple(),
                  "ucontrol.move": (
                                       (Param.INPUT, Type.NUM),
                                   ) * 2,
                  "ucontrol.approach": (
                                           (Param.INPUT, Type.NUM),
                                       ) * 3,
                  "ucontrol.boost": (
                      (Param.INPUT, Type.NUM),
                  ),
                  "ucontrol.target": (
                                         (Param.INPUT, Type.NUM),
                                     ) * 3,
                  "ucontrol.targetp": (
                      (Param.INPUT, Type.UNIT),
                      (Param.INPUT, Type.NUM),
                  ),
                  "ucontrol.itemDrop": (
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.NUM),
                  ),
                  "ucontrol.itemTake": (
                      (Param.INPUT, Type.BLOCK),
                      (Param.INPUT, Type.ITEM_TYPE),
                      (Param.INPUT, Type.NUM)
                  ),
                  "ucontrol.payDrop": tuple(),
                  "ucontrol.payTake": (
                      (Param.INPUT, Type.NUM),
                  ),
                  "ucontrol.payEnter": tuple(),
                  "ucontrol.mine": (
                                       (Param.INPUT, Type.NUM),
                                   ) * 2,
                  "ucontrol.flag": (
                      (Param.INPUT, Type.NUM),
                  ),
                  "ucontrol.build": (
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.BLOCK_TYPE),
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM)
                  ),
                  "ucontrol.getBlock": (
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM),
                      (Param.OUTPUT, Type.BLOCK_TYPE),
                      (Param.OUTPUT, Type.BLOCK),
                  ),
                  "ucontrol.within": (
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM),
                      (Param.INPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM)
                  ),
                  "ucontrol.unbind": tuple(),

                  "uradar": (
                      (Param.CONFIG, ("any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground")),
                      (Param.CONFIG, ("any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground")),
                      (Param.CONFIG, ("any", "enemy", "ally", "player", "attacker", "flying", "boss", "ground")),
                      (Param.CONFIG, ("distance", "health", "shield", "armor", "maxHealth")),
                      (Param.UNUSED, Type.ANY),
                      (Param.INPUT, Type.NUM),
                      (Param.OUTPUT, Type.UNIT)
                  ),

                  "ulocate.ore": (
                      (Param.UNUSED, Type.ANY),
                      (Param.UNUSED, Type.ANY),
                      (Param.INPUT, Type.BLOCK_TYPE),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM),
                      (Param.UNUSED, Type.ANY)
                  ),
                  "ulocate.building": (
                      (Param.CONFIG,
                       ("core", "storage", "generator", "turret", "factory", "repair", "battery", "reactor")),
                      (Param.INPUT, Type.NUM),
                      (Param.UNUSED, Type.ANY),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.BLOCK)
                  ),
                  "ulocate.spawn": (
                      (Param.UNUSED, Type.ANY),
                      (Param.UNUSED, Type.ANY),
                      (Param.UNUSED, Type.ANY),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.BLOCK)
                  ),
                  "ulocate.damaged": (
                      (Param.UNUSED, Type.ANY),
                      (Param.UNUSED, Type.ANY),
                      (Param.UNUSED, Type.ANY),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.NUM),
                      (Param.OUTPUT, Type.BLOCK)
                  )
              }

    # return position of native functions
    NATIVES_RETURN_POS = {
                             "read": 0,
                             "getlink": 0,
                             "radar": 6
                         } | \
                         {
                             f"sensor.{property}": 0 for property in constants.SENSOR_READABLE.keys()
                         } | \
                         {
                             "lookup.block": 0,
                             "lookup.unit": 0,
                             "lookup.item": 0,
                             "lookup.liquid": 0,
                             "packcolor": 0,
                             "ucontrol.within": 3,
                             "uradar": 6
                         }

    # builtin functions
    BUILTINS = {
        "max": 2,
        "min": 2,
        "angle": 2,
        "len": 2,
        "noise": 2,
        "abs": 1,
        "log": 1,
        "log10": 1,
        "floor": 1,
        "ceil": 1,
        "sqrt": 1,
        "rand": 1,
        "sin": 1,
        "cos": 1,
        "tan": 1,
        "asin": 1,
        "acos": 1,
        "atan": 1
    }

    ALL_NATIVES = NATIVES | {
        "set": (
            (Param.OUTPUT, Type.ANY),
            (Param.INPUT, Type.ANY)
        ),

        "op": (
            (Param.CONFIG, Type.ANY),
            (Param.OUTPUT, Type.NUM),
            (Param.INPUT, Type.ANY),
            (Param.INPUT, Type.ANY)
        )
    }

    NATIVES_PARAM_COUNT = {
        "read": 3,
        "write": 3,
        "draw": 7,
        "print": 1,
        "drawflush": 1,
        "printflush": 1,
        "getlink": 2,
        "control": 6,
        "radar": 7,
        "sensor": 3,
        "set": 2,
        "op": 4,
        "wait": 1,
        "lookup": 3,
        "packcolor": 5,
        "end": 0,
        "jump": 4,
        "ubind": 1,
        "ucontrol": 6,
        "uradar": 7,
        "ulocate": 8
    }


# precalculation functions
PRECALC = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b,
    "idiv": lambda a, b: a // b,
    "mod": lambda a, b: a % b,
    "pow": lambda a, b: a ** b,
    "not": lambda a, _: not a,
    "land": lambda a, b: a and b,
    "lessThan": lambda a, b: a < b,
    "lessThanEq": lambda a, b: a <= b,
    "greaterThan": lambda a, b: a > b,
    "greaterThanEq": lambda a, b: a >= b,
    "strictEqual": lambda a, b: a == b,
    "shl": lambda a, b: a << b,
    "shr": lambda a, b: a >> b,
    "or": lambda a, b: a | b,
    "and": lambda a, b: a & b,
    "xor": lambda a, b: a ^ b,
    "flip": lambda a, _: ~a,
    "max": lambda a, b: max(a, b),
    "min": lambda a, b: min(a, b),
    "abs": lambda a, _: abs(a),
    "log": lambda a, _: math.log(a),
    "log10": lambda a, _: math.log10(a),
    "floor": lambda a, _: math.floor(a),
    "ceil": lambda a, _: math.ceil(a),
    "sqrt": lambda a, _: math.sqrt(a),
    "angle": lambda a, b: math.atan2(b, a) * 180 / math.pi,
    "length": lambda a, b: math.sqrt(a * a + b * b),
    "sin": lambda a, _: math.sin(math.radians(a)),
    "cos": lambda a, _: math.cos(math.radians(a)),
    "tan": lambda a, _: math.tan(math.radians(a)),
    "asin": lambda a, _: math.degrees(math.asin(a)),
    "acos": lambda a, _: math.degrees(math.acos(a)),
    "atan": lambda a, _: math.degrees(math.atan(a))

    # noise and rand not implemented
    # equal and notEqual are not implemented because they use type conversion
}

# jump conditions for replacement optimization
JC_REPLACE = {
    "equal": "notEqual",
    "notEqual": "equal",
    "greaterThan": "lessThanEq",
    "lessThan": "greaterThanEq",
    "greaterThanEq": "lessThan",
    "lessThanEq": "greaterThan"
}
