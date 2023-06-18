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

        return type(f"Instruction{name[0].upper()}{name[1:]}", (BaseInstruction,), {
            "__init__": __init__
        })


class Instruction(BaseInstruction):
    def __init__(self, *_):
        super().__init__("", ())

        raise ValueError("placeholder value")


InstructionRead = Instruction.create(
    "read", 3
)

InstructionWrite = Instruction.create(
    "write", 3
)

InstructionPrint = Instruction.create(
    "print", 1
)

InstructionPrintFlush = Instruction.create(
    "printflush", 1
)

InstructionSet = Instruction.create(
    "set", 2
)

InstructionOp = Instruction.create(
    "op", 4
)

InstructionJump = Instruction.create(
    "jump", 4
)

InstructionGetLink = Instruction.create(
    "getlink", 2
)

InstructionEnd = Instruction.create(
    "end", 0
)


class Label(Instruction):
    name: str

    def __init__(self, name: str):
        BaseInstruction.__init__(self, "label", (name,))

        self.name = name

    def __str__(self):
        return f"{self.name}:"
