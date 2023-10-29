from __future__ import annotations

import enum
from typing import Callable, TypeVar

from .instruction import *
from .generator import Gen
from .error import Error
from .enums import ENUMS, SENSABLE, RULES, SETPROP, EnumRadarFilter, EnumLocateType, EnumRadarSort, EnumEffect, EnumTypeImpl
from .node import Node
from .values import TypeImpl, Type, Value


class Param(enum.Enum):
    INPUT: Param = enum.auto()
    OUTPUT: Param = enum.auto()
    OUTPUT_P: Param = enum.auto()
    CONSTANT: Param = enum.auto()


class NativeInsTypeImpl(TypeImpl):
    ins: type[Instruction]
    params: list[tuple[Param, Type | str]]

    def __init__(self, ins: type[Instruction], params: list[tuple[Param, Type | str]]):
        self.ins = ins
        self.params = params

    def get(self, value: Value) -> str:
        return "null"

    def callable(self, value: Value) -> bool:
        return True

    def call(self, value: Value, node, params: list[Value]) -> Value:
        result = Value.null()

        par: list[str] = []
        out: list[tuple[Value, Value]] = []
        i = 0
        for p, t in self.params:
            if p == Param.INPUT:
                self._add_param(node, par, out, params[i], t, False)
                i += 1

            elif p == Param.OUTPUT:
                self._add_param(node, par, out, params[i], t, True)
                i += 1

            elif p == Param.OUTPUT_P:
                result = Value.variable(Gen.tmp(), t)
                par.append(result.value)

            elif p == Param.CONSTANT:
                par.append(t)

        Gen.emit(
            self.ins(*(par + ["0"] * (self.ins.num_params() - len(par))))
        )
        for dst, src in out:
            dst.set(src)

        return result

    @staticmethod
    def _add_param(node: Node, params: list[str], outputs: list[tuple[Value, Value]], param: Value, type_: Type, output: bool):
        if output:
            if param.const():
                Error.write_to_const(node, param.get())

            if type_ not in param.type():
                Error.incompatible_types(node, type_, param.type())

            result = Gen.tmp()
            params.append(result)
            outputs.append((param, Value.variable(result, type_)))

        else:
            if param.type() not in type_:
                Error.incompatible_types(node, param.type(), type_)

            params.append(param.get())

    def get_params(self, value: Value) -> list[Type]:
        return [param[1] for param in self.params if param[0] in (Param.INPUT, Param.OUTPUT)]

    def outputs(self, value: Value) -> list[int]:
        return [i for i, [param, _] in enumerate(self.params) if param == Param.OUTPUT]


T = TypeVar("T")


class NativeMultiInsTypeImpl(TypeImpl):
    instructions: dict[str, Value]
    subname_function: Callable[[list[T]], T]

    def __init__(self, instructions: dict[str, Value], subname_function: Callable[[list[T]], T]):
        self.instructions = instructions
        self.subname_function = subname_function

    def get(self, value: Value) -> str:
        return "null"

    def getattr(self, value: Value, name: str) -> Value | None:
        return self.instructions.get(name)


def native_function_value(ins: type[Instruction], params: list[Type], ret: int = -1, outputs: list[int] = None, *,
                          constants: dict[int, str] = None) -> Value:
    if constants is None:
        constants = {}

    if outputs is None:
        outputs = []

    par: list[tuple[Param, Type | str]] = []
    for i, param in enumerate(params):
        if i in constants:
            par.append((Param.CONSTANT, constants[i]))

        elif ret == i:
            par.append((Param.OUTPUT_P, param))

        elif i in outputs:
            par.append((Param.OUTPUT, param))

        else:
            par.append((Param.INPUT, param))

    return Value(Type.OBJECT, "null", type_impl=NativeInsTypeImpl(ins, par))

def native_multi_function_value(ins: type[Instruction], functions: dict[str, list[Type] |
                                                                             tuple[list[Type], int] |
                                                                             tuple[list[Type], int, list[int]] |
                                                                             tuple[list[Type], int, list[int], list[
                                                                                 int]] |
                                                                             Value],
                                subname_index: int = 0, subname_function: Callable[[list[T]], T]=None) -> Value:

    func: dict[str, Value] = {}
    for n, f in functions.items():
        if isinstance(f, list):
            func[n] = native_function_value(ins, f)

        elif isinstance(f, Value):
            func[n] = f

        elif len(f) == 4:
            unused = f[3]
            assert isinstance(unused, list)
            func[n] = native_function_value(ins, *(f[:-1]), constants={i: "0" for i in unused})

        else:
            func[n] = native_function_value(ins, *f)

        if not isinstance(f, Value):
            impl = func[n].impl()
            if isinstance(impl, NativeInsTypeImpl):
                if subname_index == -1:
                    impl.params.append((Param.CONSTANT, n))
                else:
                    impl.params.insert(subname_index, (Param.CONSTANT, n))

            else:
                raise TypeError

        else:
            impl = func[n].impl()
            if isinstance(impl, NativeInsTypeImpl):
                if subname_index == -1:
                    impl.params.append((Param.CONSTANT, n))
                else:
                    impl.params.insert(subname_index, (Param.CONSTANT, n))

            else:
                raise TypeError

    return Value(Type.OBJECT, "null", type_impl=NativeMultiInsTypeImpl(
        func, (lambda params: params[subname_index]) if subname_function is None else subname_function))


class BuiltinOperationTypeImpl(TypeImpl):
    op: str
    params: int

    def __init__(self, op: str, params: int):
        self.op = op
        self.params = params

    def get(self, value: Value) -> str:
        return "null"

    def callable(self, value: Value) -> bool:
        return True

    def call(self, value: Value, node, params: list[Value]) -> Value:
        if len(params) != self.params:
            Error.invalid_arg_count(node, len(params), self.params)

        for param in params:
            if param.type() not in Type.NUM:
                Error.incompatible_types(node, param.type(), Type.NUM)

        result = Gen.tmp()
        Gen.emit(
            InstructionOp(self.op, result, *params, *([0] * (2 - len(params))))
        )
        return Value.variable(result, Type.NUM)

    def get_params(self, value: Value) -> list[Type]:
        return [Type.NUM] * self.params


BUILTIN_VARIABLES = {
    "@this": Value.variable("@this", Type.BLOCK, True),
    "@thisx": Value.variable("@thisx", Type.NUM, True),
    "@thisy": Value.variable("@thisy", Type.NUM, True),
    "@ipt": Value.variable("@ipt", Type.NUM, True),
    "@timescale": Value.variable("@ipt", Type.NUM, True),
    "@counter": Value.variable("@counter", Type.NUM, True),
    "@links": Value.variable("@links", Type.NUM, True),
    "@unit": Value.variable("@unit", Type.UNIT, False),
    "@time": Value.variable("@time", Type.NUM, True),
    "@tick": Value.variable("@tick", Type.NUM, True),
    "@second": Value.variable("@second", Type.NUM, True),
    "@minute": Value.variable("@minute", Type.NUM, True),
    "@waveNumber": Value.variable("@waveNumber", Type.NUM, True),
    "@waveTime": Value.variable("@waveTime", Type.NUM, True),
    "@mapw": Value.variable("@mapw", Type.NUM, True),
    "@maph": Value.variable("@maph", Type.NUM, True),

    "@ctrlProcessor": Value.variable("@ctrlProcessor", Type.CONTROLLER, True),
    "@ctrlPlayer": Value.variable("@ctrlPlayer", Type.CONTROLLER, True),
    "@ctrlCommand": Value.variable("@ctrlCommand", Type.CONTROLLER, True),

    "@solid": Value.variable("@solid", Type.BLOCK_TYPE, True),

    "_": Value.variable("_", Type.ANY, False)
}

BUILTIN_CONSTANTS = {
    "true": Value.variable("true", Type.NUM, True),
    "false": Value.variable("false", Type.NUM, True),
    "null": Value.variable("null", Type.NULL, True)
}

BUILTIN_FUNCTIONS = {
    "read": native_function_value(InstructionRead, [Type.NUM, Type.BLOCK, Type.NUM], 0),
    "write": native_function_value(InstructionWrite, [Type.NUM | Type.COLOR, Type.BLOCK, Type.NUM]),
    "draw": native_multi_function_value(
        InstructionDraw,
        {
            "clear": [Type.NUM] * 3,
            "color": [Type.NUM] * 4,
            "col": [Type.NUM],
            "stroke": [Type.NUM],
            "line": [Type.NUM] * 4,
            "rect": [Type.NUM] * 4,
            "lineRect": [Type.NUM] * 4,
            "poly": [Type.NUM] * 5,
            "linePoly": [Type.NUM] * 5,
            "triangle": [Type.NUM] * 6,
            "image": [Type.NUM, Type.NUM, Type.CONTENT, Type.NUM, Type.BLOCK],
        }
    ),
    "print": native_function_value(InstructionPrint, [Type.ANY]),

    "drawflush": native_function_value(InstructionDrawFlush, [Type.BLOCK]),
    "printflush": native_function_value(InstructionPrintFlush, [Type.BLOCK]),
    "getlink": native_function_value(InstructionGetLink, [Type.BLOCK, Type.NUM], 0),
    "control": native_multi_function_value(
        InstructionControl,
        {
            "enabled": [Type.BLOCK, Type.NUM],
            "shoot": [Type.BLOCK, Type.NUM, Type.NUM, Type.NUM],
            "shootp": [Type.BLOCK, Type.UNIT, Type.NUM],
            "config": [Type.BLOCK, Type.CONTENT],
            "color": [Type.BLOCK, Type.NUM]
        }
    ),
    "radar": native_function_value(InstructionRadar, [EnumRadarFilter.type()] * 3 + [EnumRadarSort.type(), Type.BLOCK,
                                                                                   Type.NUM, Type.UNIT], 6),
    "sensor": native_multi_function_value(
        InstructionSensor,
        {name: ([type_, Type.BLOCK | Type.UNIT], 0) for name, type_ in SENSABLE.items()},
        -1, lambda params: params[-1][1:]
    ),

    "lookup": native_multi_function_value(
        InstructionLookup,
        {
            "block": ([Type.BLOCK_TYPE, Type.NUM], 0),
            "unit": ([Type.UNIT_TYPE, Type.NUM], 0),
            "item": ([Type.ITEM_TYPE, Type.NUM], 0),
            "liquid": ([Type.LIQUID_TYPE, Type.NUM], 0)
        }
    ),
    "packcolor": native_function_value(InstructionPackColor, [Type.NUM] * 5, 0),

    "wait": native_function_value(InstructionWait, [Type.NUM]),
    "stop": native_function_value(InstructionStop, []),
    "end": native_function_value(InstructionEnd, []),

    "ubind": native_function_value(InstructionUBind, [Type.UNIT_TYPE]),
    "ucontrol": native_multi_function_value(
        InstructionUControl,
        {
            "idle": [],
            "stop": [],
            "move": [Type.NUM] * 2,
            "approach": [Type.NUM] * 3,
            "pathfind": [Type.NUM] * 2,
            "autoPathfind": [],
            "boost": [Type.NUM],
            "target": [Type.NUM] * 3,
            "targetp": [Type.UNIT, Type.NUM],
            "itemDrop": [Type.BLOCK, Type.NUM],
            "itemTake": [Type.BLOCK, Type.ITEM_TYPE, Type.NUM],
            "payDrop": [],
            "payTake": [Type.NUM],
            "payEnter": [],
            "mine": [Type.NUM] * 2,
            "flag": [Type.NUM],
            "build": [Type.NUM, Type.NUM, Type.BLOCK_TYPE, Type.NUM, Type.CONTENT | Type.BLOCK],
            "getBlock": native_function_value(
                InstructionUControl,
                [Type.NUM, Type.NUM, Type.BLOCK_TYPE, Type.BLOCK, Type.NUM],
                3, [2]
            ),
            "within": ([Type.NUM] * 4, 3),
            "unbind": []
        }
    ),
    "uradar": native_function_value(InstructionURadar, [EnumRadarFilter.type()] * 3 + [EnumRadarSort.type(), Type.ANY,
                                                                                     Type.NUM, Type.UNIT], 6,
                                    constants={5: "0"}),
    "ulocate": native_multi_function_value(
        InstructionULocate,
        {
            "ore": ([Type.ANY, Type.ANY, Type.BLOCK_TYPE, Type.NUM, Type.NUM, Type.NUM, Type.NUM], 3, [4, 5], [0, 1]),
            "building": ([EnumLocateType.type(), Type.NUM, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK], 5,
                         [3, 4, 6], [2]),
            "spawn": (
            [Type.ANY, Type.ANY, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK], 3, [4, 5, 6], [0, 1, 2]),
            "damaged": (
            [Type.ANY, Type.ANY, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK], 3, [4, 5, 6], [0, 1, 2])
        }
    ),

    "getblock": native_multi_function_value(
        InstructionGetBlock,
        {
            "floor": ([Type.BLOCK_TYPE, Type.NUM, Type.NUM], 0),
            "ore": ([Type.BLOCK_TYPE, Type.NUM, Type.NUM], 0),
            "block": ([Type.BLOCK_TYPE, Type.NUM, Type.NUM], 0),
            "building": ([Type.BLOCK, Type.NUM, Type.NUM], 0)
        }
    ),
    "setblock": native_multi_function_value(
        InstructionSetBlock,
        {
            "floor": [Type.BLOCK_TYPE, Type.NUM, Type.NUM],
            "ore": [Type.BLOCK_TYPE, Type.NUM, Type.NUM],
            "block": [Type.BLOCK_TYPE, Type.NUM, Type.NUM, Type.TEAM, Type.NUM]
        }
    ),
    "spawn": native_function_value(InstructionSpawn, [Type.UNIT_TYPE, Type.NUM, Type.NUM, Type.NUM, Type.TEAM,
                                                      Type.UNIT], 5),
    "status": native_multi_function_value(
        InstructionStatus,
        {
            "apply": native_function_value(InstructionStatus, [Type.NUM, EnumEffect.type(), Type.UNIT, Type.NUM],
                                           constants={0: "true"}),
            "clear": native_function_value(InstructionStatus, [Type.NUM, EnumEffect.type(), Type.UNIT, Type.NUM],
                                           constants={0: "false", 3: 0})
        }
    ),
    "spawnwave": native_function_value(InstructionSpawnWave, [Type.NUM, Type.NUM, Type.NUM]),
    "setrule": native_multi_function_value(
        InstructionSetRule,
        {rule: [[Type.NUM, Type.TEAM] if param else [Type.NUM]] for rule, param in RULES.items()} |
        {
            "mapArea": ([Type.ANY] + [Type.NUM] * 4, 0, [], [0])
        }
    ),
    "message": native_multi_function_value(
        InstructionMessage,
        {
            "notify": [],
            "announce": [Type.NUM],
            "toast": [Type.NUM],
            "mission": []
        }
    ),
    "cutscene": native_multi_function_value(
        InstructionCutscene,
        {
            "pan": [Type.NUM] * 3,
            "zoom": [Type.NUM],
            "stop": []
        }
    ),
    "effect": native_multi_function_value(
        InstructionEffect,
        {
            "warn": [Type.NUM] * 2,
            "cross": [Type.NUM] * 2,
            "blockFall": ([Type.NUM, Type.NUM, Type.ANY, Type.ANY, Type.BLOCK], -1, [], [2, 3]),
            "placeBlock": [Type.NUM, Type.NUM, Type.NUM],
            "placeBlockSpark": [Type.NUM, Type.NUM, Type.NUM],
            "breakBlock": [Type.NUM, Type.NUM, Type.NUM],
            "spawn": [Type.NUM] * 2,
            "trail": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "breakProp": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "smokeCloud": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "vapor": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "hit": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "hitSquare": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "shootSmall": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "shootBig": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "smokeSmall": [Type.NUM] * 3,
            "smokeBig": [Type.NUM] * 3,
            "smokeColor": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "smokeSquare": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "smokeSquareBig": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "spark": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "sparkBig": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "sparkShoot": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "sparkShootBig": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "drill": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "drillBig": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "lightBlock": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "explosion": [Type.NUM] * 3,
            "smokePuff": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "sparkExplosion": ([Type.NUM, Type.NUM, Type.NUM, Type.COLOR], -1, [], [2]),
            "crossExplosion": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "wave": [Type.NUM, Type.NUM, Type.NUM, Type.COLOR],
            "bubble": [Type.NUM] * 2
        }
    ),
    "explosion": native_function_value(InstructionExplosion, [Type.TEAM] + [Type.NUM] * 7),
    "setrate": native_function_value(InstructionSetRate, [Type.NUM]),
    "fetch": native_multi_function_value(
        InstructionFetch,
        {
            "unit": ([Type.UNIT, Type.TEAM, Type.NUM], 0),
            "unitCount": ([Type.NUM, Type.TEAM], 0),
            "player": ([Type.UNIT, Type.TEAM, Type.NUM], 0),
            "playerCount": ([Type.NUM, Type.TEAM], 0),
            "core": ([Type.BLOCK, Type.TEAM, Type.NUM], 0),
            "coreCount": ([Type.NUM, Type.TEAM], 0),
            "build": ([Type.BLOCK, Type.TEAM, Type.NUM, Type.BLOCK_TYPE], 0),
            "buildCount": ([Type.NUM, Type.TEAM, Type.ANY, Type.BLOCK_TYPE], 0, [], [2])
        }
    ),
    "sync": native_function_value(InstructionSync, [Type.ANY]),
    "getflag": native_function_value(InstructionGetFlag, [Type.NUM, Type.STR], 0),
    "setflag": native_function_value(InstructionSetFlag, [Type.STR, Type.NUM]),
    "setprop": native_multi_function_value(
        InstructionSetProp,
        {prop: [type_, Type.BLOCK | Type.UNIT] for prop, type_ in SETPROP.items()}
    )
}
PRIVATE_BUILTIN_FUNCTIONS = {
    "set": native_function_value(InstructionSet, [Type.ANY] * 2, 0),
    "op": native_function_value(InstructionOp, [Type.ANY] * 4, 1),
    "noop": native_function_value(InstructionNoop, []),
    "jump": native_function_value(InstructionJump, [Type.ANY] * 4),
    "label": native_function_value(Label, [Type.ANY]),
}
BaseInstruction.Param = Param
BaseInstruction.NativeInsTypeImpl = NativeInsTypeImpl
BaseInstruction.NativeMultiInsTypeImpl = NativeMultiInsTypeImpl
BaseInstruction.Builtins = BUILTIN_FUNCTIONS | PRIVATE_BUILTIN_FUNCTIONS
BaseInstruction.Value = Value

_OPERATIONS = {
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

BUILTIN_OPERATIONS = {
    op: Value(Type.OBJECT, "null", type_impl=BuiltinOperationTypeImpl(op, params)) for op, params in _OPERATIONS.items()
}


def _make_builtin_enums():
    result = {}
    for e in ENUMS:
        impl = e.impl()
        assert isinstance(impl, EnumTypeImpl)
        result[impl.name] = e
    return result

BUILTIN_ENUMS = _make_builtin_enums()

BUILTINS: dict[str, Value] = BUILTIN_VARIABLES | BUILTIN_CONSTANTS | BUILTIN_FUNCTIONS | BUILTIN_OPERATIONS | BUILTIN_ENUMS
