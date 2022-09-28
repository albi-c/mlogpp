import enum


class Instruction:
    def __add__(self, other):
        if isinstance(other, Instruction):
            return Instructions([self, other])
        elif isinstance(other, Instructions):
            return Instructions([self] + other.ins)

    def iter(self) -> tuple:
        return self,


class MInstructionType(enum.Enum):
    READ = enum.auto()
    WRITE = enum.auto()
    DRAW = enum.auto()
    PRINT = enum.auto()
    DRAWFLUSH = enum.auto()
    PRINTFLUSH = enum.auto()
    GETLINK = enum.auto()
    CONTROL = enum.auto()
    RADAR = enum.auto()
    SENSOR = enum.auto()
    SET = enum.auto()
    OP = enum.auto()
    WAIT = enum.auto()
    LOOKUP = enum.auto()
    PACKCOLOR = enum.auto()
    END = enum.auto()
    JUMP = enum.auto()
    UBIND = enum.auto()
    UCONTROL = enum.auto()
    URADAR = enum.auto()
    ULOCATE = enum.auto()


class MInstruction(Instruction):
    type: MInstructionType
    params: list[str]

    def __init__(self, type_: MInstructionType, params: list[str]):
        self.type = type_
        self.params = params

    def __str__(self) -> str:
        return f"{self.type.name.lower()} {' '.join(map(str, self.params))}"


class MppInstructionLabel(Instruction):
    name: str

    def __init__(self, name: str):
        self.name = str(name)

    def __str__(self) -> str:
        return f"{self.name}:"


class MppInstructionJump(Instruction):
    label: str

    def __init__(self, label: str):
        self.label = str(label)

    def __str__(self) -> str:
        return f"jump {self.label} always _ _"


# class MppInstructionCJump(Instruction):
#     label: str
#     cond: str
#
#     def __init__(self, label: str, cond: str):
#         self.label = str(label)
#         self.cond = str(cond)
#
#     def __str__(self) -> str:
#         return f"jump {self.label} "


class MppInstructionOJump(Instruction):
    label: str
    op1: str
    op: str
    op2: str

    def __init__(self, label: str, op1: str, op: str, op2: str):
        self.label = str(label)
        self.op1 = str(op1)
        self.op = str(op)
        self.op2 = str(op2)

    def __str__(self) -> str:
        return f"jump {self.label} {self.op1} {self.op} {self.op2}"


class Instructions:
    def __init__(self, ins: list[Instruction] | None = None):
        self.ins = [] if ins is None else ins

    def __add__(self, other):
        if isinstance(other, Instruction):
            return Instructions(self.ins + [other])
        elif isinstance(other, Instructions):
            return Instructions(self.ins + other.ins)

    def __iadd__(self, other):
        if isinstance(other, Instruction):
            self.ins.append(other)
        elif isinstance(other, Instructions):
            self.ins += other.ins

        return self

    def iter(self) -> tuple:
        return tuple(self.ins)
