from __future__ import annotations

from .values import Type, Value, CallableValue, VariableValue, NullValue, SettableValue
from .instruction import *
from .generator import Gen
from .error import Error
from .enums import *
from .scope import Scope


class NativeFunctionValue(CallableValue):
    ins: type[Instruction]
    params: list[Type]
    ret: int
    constants: dict[int, str]

    def __init__(self, ins: type[Instruction], params: list[Type], ret: int = -1, *, constants: dict[int, str] = None):

        super().__init__(Type.function(params, params[ret] if ret >= 0 else Type.NULL))

        self.ins = ins
        self.params = params
        self.ret = ret
        self.constants = constants if constants is not None else {}

    def __eq__(self, other):
        if isinstance(other, NativeFunctionValue):
            return self.ins == other.ins and self.params == other.params and self.ret == other.ret

    def get(self) -> str:
        return str(self.type())

    def call(self, node: 'Node', params: list[Value]) -> Value:
        if self.ret >= 0:
            ret = Gen.tmp()
            par = []
            diff = 0
            for i, param in enumerate(self.params):
                if i in self.constants:
                    par.append(self.constants[i])
                    diff += 1

                elif i == self.ret:
                    par.append(ret)
                    diff += 1

                else:
                    i -= diff

                    if params[i].type() not in param:
                        Error.incompatible_types(node, params[i].type(), param)

                    par.append(params[i].get())

            par += [0] * (self.ins.num_params() - len(par))

            Gen.emit(self.ins(*par))
            return VariableValue(ret, self.params[self.ret])

        else:
            par = []
            diff = 0
            for i, param in enumerate(self.params):
                if i in self.constants:
                    par.append(self.constants[i])
                    diff += 1

                else:
                    i -= diff

                    if params[i].type() not in param:
                        Error.incompatible_types(node, params[i].type(), param)

                    par.append(params[i].get())

            par += [0] * (self.ins.num_params() - len(par))

            Gen.emit(self.ins(*par))
            return NullValue()

    def get_params(self) -> list[Type]:
        return [param for i, param in enumerate(self.params) if i != self.ret and i not in self.constants]


class NativeMultiReturnFunctionValue(CallableValue):
    ins: type[Instruction]
    params: list[Type]
    ret: list[int]
    primary_ret: int
    constants: dict[int, str]

    def __init__(self, ins: type[Instruction], params: list[Type], ret: list[int], primary_ret: int = -1, *,
                 constants: dict[int, str] = None):

        super().__init__(Type.function(params, [params[i] for i in ret]))

        self.ins = ins
        self.params = params
        self.ret = ret
        self.primary_ret = primary_ret
        self.constants = constants if constants is not None else {}

    def __eq__(self, other):
        if isinstance(other, NativeFunctionValue):
            return self.ins == other.ins and self.params == other.params and self.ret == other.ret

    def get(self) -> str:
        return str(self.type())

    def call(self, node: 'Node', params: list[Value]) -> Value:
        par: list[str] = []
        out: list[tuple[str, SettableValue, Type]] = []
        result = None
        diff = 0
        for i, param in self.params:
            if i in self.constants:
                par.append(self.constants[i])
                diff += 1

            elif i == self.primary_ret:
                result = Gen.tmp()
                par.append(result)
                diff += 1

            elif i in self.ret:
                i -= diff

                p = params[i]

                if param not in p.type():
                    Error.incompatible_types(node, param, p.type())

                if isinstance(p, SettableValue) and not p.const():
                    res = Gen.tmp()
                    par.append(res)
                    out.append((res, p, param))

                else:
                    Error.write_to_const(node, str(p))

            else:
                i -= diff

                if params[i].type() not in param:
                    Error.incompatible_types(node, params[i].type(), param)

                par.append(params[i].get())

        Gen.emit(self.ins(*par))

        for res, param, type_ in out:
            param.set(VariableValue(res, type_))

        if self.primary_ret >= 0:
            assert result is not None
            return VariableValue(result, self.params[self.primary_ret])

        return NullValue()

    def get_params(self) -> list[Type]:
        return [param for i, param in enumerate(self.params) if i != self.primary_ret and i not in self.constants]


class NativeMultiFunctionValue(Value):
    functions: dict[str, NativeFunctionValue | NativeMultiReturnFunctionValue]

    def __init__(self, ins: type[Instruction],
                 functions: dict[str, list[Type] | tuple[list[Type], int] | NativeMultiReturnFunctionValue]):

        super().__init__(Type.OBJECT)

        self.functions = {}
        for name, func in functions.items():
            if isinstance(func, NativeMultiReturnFunctionValue):
                self.functions[name] = func

            elif isinstance(func, list):
                self.functions[name] = NativeFunctionValue(ins, [Type.ANY] + func, constants={0: name})

            elif isinstance(func, tuple):
                self.functions[name] = NativeFunctionValue(ins, [Type.ANY] + func[0], func[1], constants={0: name})

            else:
                raise ValueError("Invalid function")

    def __eq__(self, other):
        if isinstance(other, NativeMultiFunctionValue):
            return self.functions == other.functions

        return False

    def get(self) -> str:
        return str(self.type())

    def getattr(self, name: str) -> Value | None:
        return self.functions.get(name)


class NativeMultiReturnMultiFunctionValue(Value):
    functions: dict[str, NativeMultiReturnFunctionValue]

    def __init__(self, ins: type[Instruction],
                 functions: dict[str, tuple[list[Type], list[int]] | tuple[list[Type], list[int], int] |
                                 tuple[list[Type], list[int], int, list[int]]]):

        super().__init__(Type.OBJECT)

        self.functions = {}
        for name, func in functions.items():
            if len(func) == 2:
                self.functions[name] = NativeMultiReturnFunctionValue(ins, [Type.ANY] + func[0], func[1],
                                                                      constants={0: name})

            elif len(func) == 3:
                primary_ret = func[2]
                assert isinstance(primary_ret, int)
                self.functions[name] = NativeMultiReturnFunctionValue(ins, [Type.ANY] + func[0], func[1], primary_ret,
                                                                      constants={0: name})

            elif len(func) == 4:
                primary_ret = func[2]
                skipped = func[3]
                assert isinstance(primary_ret, int)
                assert isinstance(skipped, list)
                self.functions[name] = NativeMultiReturnFunctionValue(ins, [Type.ANY] + func[0], func[1], primary_ret,
                                                                      constants={0: name} | {i: "0" for i in skipped})

            else:
                raise ValueError("Invalid function")

    def __eq__(self, other):
        if isinstance(other, NativeMultiReturnMultiFunctionValue):
            return self.functions == other.functions

        return False

    def get(self) -> str:
        return str(self.type())

    def getattr(self, name: str) -> Value | None:
        return self.functions.get(name)


BUILTIN_VARIABLES = {
    "@this": VariableValue("@this", Type.BLOCK, True),
    "@thisx": VariableValue("@thisx", Type.NUM, True),
    "@thisy": VariableValue("@thisy", Type.NUM, True),
    "@ipt": VariableValue("@ipt", Type.NUM, True),
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
    "read": NativeFunctionValue(InstructionRead, [Type.NUM, Type.BLOCK, Type.NUM], 0),
    "write": NativeFunctionValue(InstructionWrite, [Type.NUM, Type.BLOCK, Type.NUM]),
    "draw": NativeMultiFunctionValue(
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
    "print": NativeFunctionValue(InstructionPrint, [Type.ANY]),

    "drawflush": NativeFunctionValue(InstructionDrawFlush, [Type.BLOCK]),
    "printflush": NativeFunctionValue(InstructionPrintFlush, [Type.BLOCK]),
    "getlink": NativeFunctionValue(InstructionGetLink, [Type.BLOCK, Type.NUM], 0),
    "control": NativeMultiFunctionValue(
        InstructionControl,
        {
            "enabled": [Type.BLOCK, Type.NUM],
            "shoot": [Type.BLOCK, Type.NUM, Type.NUM, Type.NUM],
            "shootp": [Type.BLOCK, Type.UNIT, Type.NUM],
            "config": [Type.BLOCK, Type.CONTENT],
            "color": [Type.BLOCK, Type.NUM]
        }
    ),
    "radar": NativeFunctionValue(InstructionRadar, [EnumRadarFilter.type] * 3 + [EnumRadarSort.type, Type.BLOCK,
                                                                                 Type.NUM, Type.UNIT], 6),
    "sensor": NativeMultiFunctionValue(
        InstructionSensor,
        {name: ([type_, Type.BLOCK | Type.UNIT], 0) for name, type_ in SENSABLE.items()}
    ),

    "lookup": NativeMultiFunctionValue(
        InstructionLookup,
        {
            "block": ([Type.BLOCK_TYPE, Type.NUM], 0),
            "unit": ([Type.UNIT_TYPE, Type.NUM], 0),
            "item": ([Type.ITEM_TYPE, Type.NUM], 0),
            "liquid": ([Type.LIQUID_TYPE, Type.NUM], 0)
        }
    ),
    "packcolor": NativeFunctionValue(InstructionPackColor, [Type.NUM] * 5, 0),

    "wait": NativeFunctionValue(InstructionWait, [Type.NUM]),
    "stop": NativeFunctionValue(InstructionStop, []),
    "end": NativeFunctionValue(InstructionEnd, []),

    "ubind": NativeFunctionValue(InstructionUBind, [Type.UNIT_TYPE]),
    "ucontrol": NativeMultiFunctionValue(
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
            "getBlock": NativeMultiReturnFunctionValue(
                InstructionUControl,
                [Type.NUM, Type.NUM, Type.BLOCK_TYPE, Type.BLOCK, Type.NUM],
                [2], 3
            ),
            "within": ([Type.NUM] * 4, 3),
            "unbind": []
        }
    ),
    "uradar": NativeFunctionValue(InstructionRadar, [EnumRadarFilter.type] * 3 + [EnumRadarSort.type, Type.BLOCK,
                                                                                  Type.ANY, Type.NUM, Type.UNIT], 7,
                                  constants={5: "0"}),
    "ulocate": NativeMultiReturnMultiFunctionValue(
        InstructionULocate,
        {
            "ore": ([Type.ANY, Type.ANY, Type.BLOCK_TYPE, Type.NUM, Type.NUM, Type.NUM, Type.NUM], [4, 5], 3, [0, 1]),
            "building": ([EnumLocateType.type, Type.NUM, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK],
                         [4, 5, 6], 3, [2]),
            "spawn": ([Type.ANY, Type.ANY, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK], [4, 5, 6], 3, [0, 1, 2]),
            "damaged": ([Type.ANY, Type.ANY, Type.ANY, Type.NUM, Type.NUM, Type.NUM, Type.BLOCK], [4, 5, 6], 3, [0, 1, 2])
        }
    )

    # TODO: world processor functions
}

# TODO: `op` instruction function-like operations (abs, log, ...)

BUILTIN_ENUMS = {
    enum.name: enum for enum in ENUMS
}

BUILTINS = BUILTIN_VARIABLES | BUILTIN_CONSTANTS | BUILTIN_FUNCTIONS | BUILTIN_ENUMS
