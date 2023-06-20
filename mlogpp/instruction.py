from __future__ import annotations

from .error import InternalError


class BaseInstruction:
    name: str
    params: list[str]

    def __init__(self, name: str, params: tuple):
        self.name = name
        self.params = [str(param) for param in params]

    def __str__(self):
        return f"{self.name} {' '.join(self.params)}"

    def __eq__(self, other):
        if isinstance(other, BaseInstruction):
            return self.name == other.name and self.params == other.params

        return False

    @classmethod
    def create(cls, name: str, n_params: int) -> type[Instruction]:
        def __init__(self, *params):
            BaseInstruction.__init__(self, name, params)

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

    def __init__(self, *_):
        super().__init__("", ())

        raise RuntimeError("placeholder function")

    @staticmethod
    def num_params() -> int:
        raise RuntimeError("placeholder function")


InstructionRead = Instruction.create("read", 3)
InstructionWrite = Instruction.create("write", 3)
InstructionDraw = Instruction.create("draw", 7)
InstructionPrint = Instruction.create("print", 1)

InstructionDrawFlush = Instruction.create("drawflush", 1)
InstructionPrintFlush = Instruction.create("printflush", 1)
InstructionGetLink = Instruction.create("getlink", 2)
InstructionControl = Instruction.create("control", 6)
InstructionRadar = Instruction.create("radar", 7)
InstructionSensor = Instruction.create("sensor", 3)

InstructionSet = Instruction.create("set", 2)
InstructionOp = Instruction.create("op", 4)
InstructionLookup = Instruction.create("lookup", 3)
InstructionPackColor = Instruction.create("packcolor", 5)

InstructionWait = Instruction.create("wait", 1)
InstructionStop = Instruction.create("stop", 0)
InstructionEnd = Instruction.create("end", 0)
InstructionJump = Instruction.create("jump", 4)

InstructionUBind = Instruction.create("ubind", 1)
InstructionUControl = Instruction.create("ucontrol", 6)
InstructionURadar = Instruction.create("uradar", 7)
InstructionULocate = Instruction.create("ulocate", 8)

InstructionGetBlock = Instruction.create("getblock", 4)
InstructionSetBlock = Instruction.create("setblock", 6)
InstructionSpawn = Instruction.create("spawn", 6)
InstructionStatus = Instruction.create("status", 4)
InstructionSpawnWave = Instruction.create("spawnwave", 3)
InstructionSetRule = Instruction.create("setrule", 6)
InstructionMessage = Instruction.create("message", 2)
InstructionCutscene = Instruction.create("cutscene", 4)
InstructionExplosion = Instruction.create("explosion", 8)
InstructionSetRate = Instruction.create("setrate", 1)
InstructionFetch = Instruction.create("fetch", 5)
InstructionGetFlag = Instruction.create("getflag", 2)
InstructionSetFlag = Instruction.create("setflag", 2)
InstructionSetProp = Instruction.create("setprop", 3)

InstructionNoop = Instruction.create("noop", 0)


class Label(Instruction):
    name: str

    def __init__(self, name: str):
        BaseInstruction.__init__(self, "label", (name,))

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
