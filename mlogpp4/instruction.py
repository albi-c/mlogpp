from __future__ import annotations

from .error import InternalError


class BaseInstruction:
    name: str
    params: tuple

    def __init__(self, name: str, params: tuple):
        self.name = name
        self.params = params

    def __str__(self):
        return f"{self.name} {' '.join(map(str, self.params))}"

    @classmethod
    def create(cls, name: str, n_params: int) -> type:
        def __init__(self, *params):
            BaseInstruction.__init__(self, name, params)

            if len(params) != n_params:
                InternalError.invalid_arg_count(self.name, len(params), n_params)

        def num_params() -> int:
            return n_params

        return type(f"Instruction{name[0].upper()}{name[1:]}", (BaseInstruction,), {
            "__init__": __init__,
            "num_params": num_params,
        })


class Instruction(BaseInstruction):
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

InstructionNoop = Instruction.create("noop", 0)

# TODO: world instructions


class Label(Instruction):
    name: str

    def __init__(self, name: str):
        BaseInstruction.__init__(self, "label", (name,))

        self.name = name

    def __str__(self):
        return f"{self.name}:"