from __future__ import annotations

import enum
import math
import typing

from .values import Type, Value, CallableValue, VariableValue, NullValue, SettableValue, NumberValue
from .instruction import *
from .generator import Gen
from .error import Error
from .enums import *
from .scope import Scope


class Param(Enum):
    INPUT = enum.auto()
    OUTPUT = enum.auto()
    OUTPUT_P = enum.auto()
    CONSTANT = enum.auto()


class NativeFunctionValue(CallableValue):
    ins: type[Instruction]
    params: list[tuple[Param, Type | str]]

    def __init__(self, ins: type[Instruction], params: list[tuple[Param, Type | str]]):
        super().__init__(Type.function([param[1] for param in params if param[0] == Param.INPUT],
                                       [param[1] for param in params if param[0] in (Param.OUTPUT, Param.OUTPUT_P)]))

        self.ins = ins
        self.params = params

    def __eq__(self, other):
        if isinstance(other, NativeFunctionValue):
            return self.ins == other.ins and self.params == other.params

        return False

    def get(self) -> str:
        return "null"

    def call(self, node: 'Node', params: list[Value]) -> Value:
        result = NullValue()

        par: list[str] = []
        out: list[tuple[VariableValue, SettableValue]] = []
        i = 0
        for p, t in self.params:
            if p == Param.INPUT:
                self._add_param(node, par, out, params[i], t, False)
                i += 1

            elif p == Param.OUTPUT:
                self._add_param(node, par, out, params[i], t, True)
                i += 1

            elif p == Param.OUTPUT_P:
                result = VariableValue(Gen.tmp(), t)
                par.append(result.name)

            elif p == Param.CONSTANT:
                par.append(t)

            else:
                raise ValueError("Invalid function")

        Gen.emit(
            self.ins(*(par + ["0"] * (self.ins.num_params() - len(par))))
        )
        for res, val in out:
            val.set(res)

        return result

    def get_params(self) -> list[Type]:
        return [param[1] for param in self.params if param[0] in (Param.INPUT, Param.OUTPUT)]

    def outputs(self) -> list[int]:
        return [i for i, [param, _] in enumerate(self.params) if param == Param.OUTPUT]

    @staticmethod
    def _add_param(node: 'Node', params: list[str], outputs: list[tuple[VariableValue, SettableValue]],
                   param: Value, type_: Type, output: bool):

        if output:
            if type_ not in param.type():
                Error.incompatible_types(node, type_, param.type())

            if isinstance(param, SettableValue) and not param.const():
                result = Gen.tmp()
                params.append(result)
                outputs.append((VariableValue(result, type_), param))

            else:
                Error.write_to_const(node, str(param))

        else:
            if param.type() not in type_:
                Error.incompatible_types(node, param.type(), type_)

            params.append(param.get())


class NativeMultiFunctionValue(Value):
    functions: dict[str, Value]

    def __init__(self, functions: dict[str, Value]):
        super().__init__(Type.OBJECT)

        self.functions = functions

    def __eq__(self, other):
        if isinstance(other, NativeMultiFunctionValue):
            return self.functions == other.functions

        return False

    def get(self) -> str:
        return "null"

    def getattr(self, name: str) -> Value | None:
        return self.functions.get(name)


def native_function_value(ins: type[Instruction], params: list[Type], ret: int = -1, outputs: list[int] = None, *,
                          constants: dict[int, str] = None) -> NativeFunctionValue:

    if constants is None:
        constants = {}

    if outputs is None:
        outputs = []

    par = []
    for i, param in enumerate(params):
        if i in constants:
            par.append((Param.CONSTANT, constants[i]))

        elif ret == i:
            par.append((Param.OUTPUT_P, param))

        elif i in outputs:
            par.append((Param.OUTPUT, param))

        else:
            par.append((Param.INPUT, param))

    return NativeFunctionValue(ins, par)


def native_multi_function_value(ins: type[Instruction], functions: dict[str, list[Type] |
                                                                        tuple[list[Type], int] |
                                                                        tuple[list[Type], int, list[int]] |
                                                                        tuple[list[Type], int, list[int], list[int]] |
                                                                        NativeFunctionValue]) -> NativeMultiFunctionValue:

    func = {}
    for n, f in functions.items():
        if isinstance(f, list):
            func[n] = native_function_value(ins, f)

        elif isinstance(f, NativeFunctionValue):
            func[n] = f

        elif len(f) == 4:
            unused = f[3]
            assert isinstance(unused, list)
            func[n] = native_function_value(ins, *(f[:-1]), constants={i: "0" for i in unused})

        else:
            func[n] = native_function_value(ins, *f)

        if not isinstance(f, NativeFunctionValue):
            func[n].params = [(Param.CONSTANT, n)] + func[n].params

    return NativeMultiFunctionValue(func)


class BuiltinOperationValue(CallableValue):
    op: str
    params: int

    PRECALC: dict[str, typing.Callable[[int | float, int | float], int | float]] = {
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
    }

    def __init__(self, op: str, params: int):
        super().__init__(Type.function([Type.NUM] * params, Type.NUM))

        self.op = op
        self.params = params

    def __eq__(self, other):
        if isinstance(BuiltinOperationValue, other):
            return self.op == other.op and self.params == other.params

        return False

    def get(self) -> str:
        return "null"

    def call(self, node: 'Node', params: list[Value]) -> Value:
        if len(params) != self.params:
            Error.invalid_arg_count(node, len(params), self.params)

        for param in params:
            if param.type() not in Type.NUM:
                Error.incompatible_types(node, param.type(), Type.NUM)

        if len(params) == 1 and isinstance(params[0], NumberValue):
            try:
                result = float(self.PRECALC[self.op](params[0].value, 0))
                if result.is_integer():
                    result = int(result)
                return NumberValue(result)
            except (TypeError, ArithmeticError, KeyError):
                pass

        elif len(params) == 2 and isinstance(params[0], NumberValue) and isinstance(params[1], NumberValue):
            try:
                result = float(self.PRECALC[self.op](params[0].value, params[1].value))
                if result.is_integer():
                    result = int(result)
                return NumberValue(result)
            except (TypeError, ArithmeticError, KeyError):
                pass

        result = Gen.tmp()
        Gen.emit(
            InstructionOp(self.op, result, *params, *([0] * (2 - len(params))))
        )
        return VariableValue(result, Type.NUM)

    def get_params(self) -> list[Type]:
        return [Type.NUM] * self.params


BUILTIN_VARIABLES = {
    "@this": VariableValue("@this", Type.BLOCK, True),
    "@thisx": VariableValue("@thisx", Type.NUM, True),
    "@thisy": VariableValue("@thisy", Type.NUM, True),
    "@ipt": VariableValue("@ipt", Type.NUM, True),
    "@timescale": VariableValue("@ipt", Type.NUM, True),
    "@counter": VariableValue("@counter", Type.NUM, True),
    "@links": VariableValue("@links", Type.NUM, True),
    "@unit": VariableValue("@unit", Type.UNIT, False),
    "@time": VariableValue("@time", Type.NUM, True),
    "@tick": VariableValue("@tick", Type.NUM, True),
    "@second": VariableValue("@second", Type.NUM, True),
    "@minute": VariableValue("@minute", Type.NUM, True),
    "@waveNumber": VariableValue("@waveNumber", Type.NUM, True),
    "@waveTime": VariableValue("@waveTime", Type.NUM, True),
    "@mapw": VariableValue("@mapw", Type.NUM, True),
    "@maph": VariableValue("@maph", Type.NUM, True),

    "@ctrlProcessor": VariableValue("@ctrlProcessor", Type.CONTROLLER, True),
    "@ctrlPlayer": VariableValue("@ctrlPlayer", Type.CONTROLLER, True),
    "@ctrlCommand": VariableValue("@ctrlCommand", Type.CONTROLLER, True),

    "@solid": VariableValue("@solid", Type.BLOCK_TYPE, True)
}

BUILTIN_CONSTANTS = {
    "true": VariableValue("true", Type.NUM, True),
    "false": VariableValue("false", Type.NUM, True),
    "null": VariableValue("null", Type.NULL, True)
}

BUILTIN_FUNCTIONS = {
    "read": native_function_value(InstructionRead, [Type.NUM, Type.BLOCK, Type.NUM], 0),
    "write": native_function_value(InstructionWrite, [Type.NUM, Type.BLOCK, Type.NUM]),
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
    "radar": native_function_value(InstructionRadar, [EnumRadarFilter.type] * 3 + [EnumRadarSort.type, Type.BLOCK,
                                                                                    Type.NUM, Type.UNIT], 6),
    "sensor": native_multi_function_value(
        InstructionSensor,
        {name: ([type_, Type.BLOCK | Type.UNIT], 0) for name, type_ in SENSABLE.items()}
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
    "uradar": native_function_value(InstructionURadar, [EnumRadarFilter.type] * 3 + [EnumRadarSort.type, Type.ANY,
                                                                                     Type.NUM, Type.UNIT], 6,
                                    constants={5: "0"}),
    "ulocate": native_multi_function_value(
        InstructionULocate,
        {
            "ore": ([Type.ANY, Type.ANY, Type.BLOCK_TYPE, Type.NUM, Type.NUM, Type.NUM, Type.NUM], 3, [4, 5], [0, 1]),
            "building": ([EnumLocateType.type, Type.NUM, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK], 3,
                         [4, 5, 6], [2]),
            "spawn": ([Type.ANY, Type.ANY, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK], 3, [4, 5, 6], [0, 1, 2]),
            "damaged": ([Type.ANY, Type.ANY, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK], 3, [4, 5, 6], [0, 1, 2])
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
            "apply": native_function_value(InstructionStatus, [Type.NUM, EnumEffect.type, Type.UNIT, Type.NUM],
                                           constants={0: "true"}),
            "clear": native_function_value(InstructionStatus, [Type.NUM, EnumEffect.type, Type.UNIT],
                                           constants={0: "false"})
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
    "status": native_multi_function_value(
        InstructionStatus,
        {
            "true": native_function_value(InstructionStatus, [EnumEffect.type, Type.UNIT, Type.NUM]),
            "false": native_function_value(InstructionStatus, [EnumEffect.type, Type.UNIT])
        }
    )
}
BaseInstruction.Param = Param
BaseInstruction.NativeFunctionValue = NativeFunctionValue
BaseInstruction.NativeMultiFunctionValue = NativeMultiFunctionValue
BaseInstruction.Builtins = BUILTIN_FUNCTIONS | PRIVATE_BUILTIN_FUNCTIONS

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
    op: BuiltinOperationValue(op, params) for op, params in _OPERATIONS.items()
}

BUILTIN_ENUMS = {
    e.name: e for e in ENUMS
}

BUILTINS = BUILTIN_VARIABLES | BUILTIN_CONSTANTS | BUILTIN_FUNCTIONS | BUILTIN_OPERATIONS | BUILTIN_ENUMS
