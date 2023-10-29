from __future__ import annotations

from .error import InternalError


class BaseInstruction:
    name: str
    params: list[str]
    inputs: list[int]
    outputs: list[int]
    side_effects: bool

    Param: type = None
    NativeInsTypeImpl: type = None
    NativeMultiInsTypeImpl: type = None
    Builtins: dict[str, NativeInsTypeImpl | NativeMultiInsTypeImpl] = None
    Value: type = None

    def __init__(self, name: str, params: tuple, side_effects: bool):
        self.name = name
        self.params = [param.get() if isinstance(param, BaseInstruction.Value) else str(param) for param in params]

        val = BaseInstruction.Builtins[name]

        impl = val.impl()
        if isinstance(impl, BaseInstruction.NativeMultiInsTypeImpl):
            val = impl.instructions[impl.subname_function(self.params)]

        impl = val.impl()
        if isinstance(impl, BaseInstruction.NativeInsTypeImpl):
            self.inputs = [i for i, [param, _] in enumerate(impl.params) if param == BaseInstruction.Param.INPUT]
            self.outputs = [i for i, [param, _] in enumerate(impl.params)
                            if param in (BaseInstruction.Param.OUTPUT, BaseInstruction.Param.OUTPUT_P)]

        else:
            raise TypeError("Invalid function type")

        self.side_effects = side_effects

        for i in self.outputs:
            assert self.params[i] != "@counter", "@counter should not be written"

    def __str__(self):
        return f"{self.name} {' '.join(map(str, self.params))}"

    def __eq__(self, other):
        if isinstance(other, BaseInstruction):
            return self.name == other.name and self.params == other.params

        return False

    def __hash__(self):
        return hash((self.name, tuple(self.params)))

    @classmethod
    def create(cls, name: str, n_params: int, side_effects: bool) -> type[Instruction]:
        def __init__(self, *params):
            BaseInstruction.__init__(self, name, params, side_effects)

            if len(params) != n_params:
                InternalError.invalid_arg_count(self.name, len(params), n_params)

        def num_params() -> int:
            return n_params

        return type[Instruction](f"Instruction{name[0].upper()}{name[1:]}", (BaseInstruction,), {
            "__init__": __init__,
            "num_params": num_params,
        })


class Instruction(BaseInstruction):
    name: str
    params: list[str]
    inputs: list[int]
    outputs: list[int]
    side_effects: bool

    def __init__(self, *_):
        super().__init__("", (), True)

        raise RuntimeError("placeholder function")

    @staticmethod
    def num_params() -> int:
        raise RuntimeError("placeholder function")


InstructionRead = Instruction.create("read", 3, False)
InstructionWrite = Instruction.create("write", 3, True)
InstructionDraw = Instruction.create("draw", 7, True)
InstructionPrint = Instruction.create("print", 1, True)

InstructionDrawFlush = Instruction.create("drawflush", 1, True)
InstructionPrintFlush = Instruction.create("printflush", 1, True)
InstructionGetLink = Instruction.create("getlink", 2, False)
InstructionControl = Instruction.create("control", 6, True)
InstructionRadar = Instruction.create("radar", 7, False)
InstructionSensor = Instruction.create("sensor", 3, False)

InstructionSet = Instruction.create("set", 2, False)
InstructionOp = Instruction.create("op", 4, False)
InstructionLookup = Instruction.create("lookup", 3, False)
InstructionPackColor = Instruction.create("packcolor", 5, False)

InstructionWait = Instruction.create("wait", 1, True)
InstructionStop = Instruction.create("stop", 0, True)
InstructionEnd = Instruction.create("end", 0, True)
InstructionJump = Instruction.create("jump", 4, True)

InstructionUBind = Instruction.create("ubind", 1, True)
InstructionUControl = Instruction.create("ucontrol", 6, True)
InstructionURadar = Instruction.create("uradar", 7, False)
InstructionULocate = Instruction.create("ulocate", 8, False)

InstructionGetBlock = Instruction.create("getblock", 4, False)
InstructionSetBlock = Instruction.create("setblock", 6, True)
InstructionSpawn = Instruction.create("spawn", 6, True)

class InstructionStatus(Instruction, BaseInstruction):
    name: str
    params: list[str]
    inputs: list[int]
    outputs: list[int]
    side_effects: bool

    def __init__(self, *params):
        self.name = "status"
        self.params = [str(param) for param in params[1:]]

        val = BaseInstruction.Builtins["status"].impl().instructions[params[0]]
        impl = val.impl()

        self.inputs = [i-1 for i, [param, _] in enumerate(impl.params) if param == BaseInstruction.Param.INPUT]
        self.outputs = [i-1 for i, [param, _] in enumerate(impl.params)
                        if param in (BaseInstruction.Param.OUTPUT, BaseInstruction.Param.OUTPUT_P)]

        self.side_effects = True

    @staticmethod
    def num_params() -> int:
        return 4

InstructionSpawnWave = Instruction.create("spawnwave", 3, True)
InstructionSetRule = Instruction.create("setrule", 6, True)
InstructionMessage = Instruction.create("message", 2, True)
InstructionCutscene = Instruction.create("cutscene", 4, True)
InstructionEffect = Instruction.create("effect", 6, True)
InstructionExplosion = Instruction.create("explosion", 8, True)
InstructionSetRate = Instruction.create("setrate", 1, True)
InstructionFetch = Instruction.create("fetch", 5, False)
InstructionSync = Instruction.create("sync", 1, True)
InstructionGetFlag = Instruction.create("getflag", 2, False)
InstructionSetFlag = Instruction.create("setflag", 2, True)
InstructionSetProp = Instruction.create("setprop", 3, True)

InstructionNoop = Instruction.create("noop", 0, False)


class Label(Instruction):
    name: str

    def __init__(self, name: str):
        BaseInstruction.__init__(self, "label", (name,), True)

        self.name = name

    def __str__(self):
        return f"{self.name}:"


INSTRUCTIONS: dict[str, type[Instruction]] = {
    "read": InstructionRead,
    "write": InstructionWrite,
    "draw": InstructionDraw,
    "print": InstructionPrint,

    "drawflush": InstructionDrawFlush,
    "printflush": InstructionPrintFlush,
    "getlink": InstructionGetLink,
    "control": InstructionControl,
    "radar": InstructionRadar,
    "sensor": InstructionSensor,

    "set": InstructionSet,
    "op": InstructionOp,
    "lookup": InstructionLookup,
    "packcolor": InstructionPackColor,

    "wait": InstructionWait,
    "stop": InstructionStop,
    "end": InstructionEnd,
    "jump": InstructionJump,

    "ubind": InstructionUBind,
    "ucontrol": InstructionUControl,
    "uradar": InstructionURadar,
    "ulocate": InstructionULocate,

    "getblock": InstructionGetBlock,
    "setblock": InstructionSetBlock,
    "spawn": InstructionSpawn,
    "status": InstructionStatus,
    "spawnwave": InstructionSpawnWave,
    "setrule": InstructionSetRule,
    "message": InstructionMessage,
    "cutscene": InstructionCutscene,
    "explosion": InstructionExplosion,
    "setrate": InstructionSetRate,
    "fetch": InstructionFetch,
    "getflag": InstructionGetFlag,
    "setflag": InstructionSetFlag,
    "setprop": InstructionSetProp,

    "noop": InstructionNoop
}
