from .values import Type, Value, CallableValue, VariableValue, NullValue
from .instruction import *
from .generator import Gen
from .error import Error


class BuiltinFunctionValue(CallableValue):
    ins: type[Instruction]
    params: list[Type]
    ret: int

    def __init__(self, ins: type[Instruction], params: list[Type], ret: int = -1):
        super().__init__(Type.function(params, params[ret] if ret >= 0 else Type.NULL))

        self.ins = ins
        self.params = params
        self.ret = ret

    def __eq__(self, other):
        if isinstance(other, BuiltinFunctionValue):
            return self.ins == other.ins and self.params == other.params and self.ret == other.ret

    def get(self) -> str:
        return str(self.type())

    def call(self, node: 'Node', params: list[Value]) -> Value:
        if self.ret >= 0:
            ret = Gen.tmp()
            par = []
            for i, param in enumerate(self.params):
                if i == self.ret:
                    par.append(ret)

                else:
                    if params[i].type() not in param:
                        Error.incompatible_types(node, params[i].type(), param)

                    par.append(params[i].get())

            Gen.emit(self.ins(*par))
            return VariableValue(ret, self.type())

        else:
            par = []
            for i, param in enumerate(self.params):
                if params[i].type() not in param:
                    Error.incompatible_types(node, params[i].type(), param)

                par.append(params[i].get())

            Gen.emit(self.ins(*par))
            return NullValue()


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
    "print": BuiltinFunctionValue(InstructionPrint, [Type.ANY]),
    "printflush": BuiltinFunctionValue(InstructionPrintFlush, [Type.BLOCK]),
    "getlink": BuiltinFunctionValue(InstructionGetLink, [Type.NUM, Type.BLOCK], 1)
}

BUILTINS = BUILTIN_VARIABLES | BUILTIN_CONSTANTS | BUILTIN_FUNCTIONS
