from .values import Type, Value, CallableValue, VariableValue, NullValue
from .instruction import *
from .generator import Gen
from .error import Error
from .enums import *


class NativeFunctionValue(CallableValue):
    ins: type[Instruction]
    params: list[Type]
    ret: int
    implicit_first_param: str

    def __init__(self, ins: type[Instruction], params: list[Type], ret: int = -1, *, implicit_first_param: str = ""):
        super().__init__(Type.function(params, params[ret] if ret >= 0 else Type.NULL))

        self.ins = ins
        self.params = params
        self.ret = ret
        self.implicit_first_param = implicit_first_param

    def __eq__(self, other):
        if isinstance(other, NativeFunctionValue):
            return self.ins == other.ins and self.params == other.params and self.ret == other.ret

    def get(self) -> str:
        return str(self.type())

    def call(self, node: 'Node', params: list[Value]) -> Value:
        if self.ret >= 0:
            ret = Gen.tmp()
            par = []
            for i, param in enumerate(self.params):
                if self.implicit_first_param and i == 0:
                    par.append(self.implicit_first_param)

                elif i == self.ret:
                    par.append(ret)

                else:
                    if params[i].type() not in param:
                        Error.incompatible_types(node, params[i].type(), param)

                    par.append(params[i].get())

            par += [0] * (self.ins.num_params() - len(par))

            Gen.emit(self.ins(*par))
            return VariableValue(ret, self.params[self.ret])

        else:
            par = []
            for i, param in enumerate(self.params):
                if params[i].type() not in param:
                    Error.incompatible_types(node, params[i].type(), param)

                par.append(params[i].get())

            par += [0] * (self.ins.num_params() - len(par))

            Gen.emit(self.ins(*par))
            return NullValue()


class NativeMultiFunctionValue(Value):
    functions: dict[str, NativeFunctionValue]

    def __init__(self, ins: type[Instruction], functions: dict[str, list[Type] | tuple[list[Type], int]]):
        super().__init__(Type.OBJECT)

        self.functions = {}
        for name, func in functions.items():
            if isinstance(func, list):
                self.functions[name] = NativeFunctionValue(ins, func, implicit_first_param=name)

            else:
                self.functions[name] = NativeFunctionValue(ins, func[0], func[1], implicit_first_param=name)

    def __eq__(self, other):
        if isinstance(other, NativeMultiFunctionValue):
            return self.ins == other.ins and self.functions == other.functions

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
    "sensor": NativeFunctionValue(InstructionSensor, [EnumSensable.type, Type.NUM, Type.BLOCK | Type.UNIT]),

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
            # TODO: getBlock
            "within": ([Type.NUM] * 4, 3),
            "unbind": []
        }
    )
    # TODO: uradar, ulocate
}

# TODO: `op` instruction function-like operations (abs, log, ...)

BUILTIN_ENUMS = {
    "Sensable": EnumSensable,
    "RadarFilter": EnumRadarFilter,
    "RadarSort": EnumRadarSort
}

BUILTINS = BUILTIN_VARIABLES | BUILTIN_CONSTANTS | BUILTIN_FUNCTIONS | BUILTIN_ENUMS
