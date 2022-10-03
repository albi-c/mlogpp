import enum

from .value import *
from .error import InternalError
from .functions import Natives, Param


class Instruction:
    """
    An instruction that will be directly converted to Mindustry logic.
    """

    def __add__(self, other):
        """
        Joins the instruction with another instruction or instruction list.

        Args:
            other (Instruction | Instructions): The instruction or instruction list to be joined.

        Returns:
            The joined instructions.
        """

        if isinstance(other, Instruction):
            return Instructions([self, other])
        elif isinstance(other, Instructions):
            return Instructions([self] + other.ins)

    def iter(self) -> list['Instruction']:
        """
        Create a lists of all instructions.

        Returns:
            A list with the one element being `self`
        """

        return [self]

    def __len__(self) -> int:
        return 1

    def __str__(self):
        return ""

    def __repr__(self):
        return "Instruction()"

    def copy(self):
        return self

    def variables(self) -> list[str]:
        """
        Returns:
            All variables used by the instruction.
        """

        return self.inputs() + self.outputs()

    def inputs(self) -> list[str]:
        """
        Returns:
            All inputs of the instruction.
        """

        return []

    def outputs(self) -> list[str]:
        """
        Returns:
            All outputs of the instruction.
        """

        return []

    def is_branching(self) -> bool:
        """
        Returns:
            True if the instruction is a branch, False otherwise.
        """

        return False

    def param_replace(self, from_: str, to: str) -> None:
        """
        Replaces parameter names.

        Args:
            from_: Which names to replace.
            to: What to replace them with.
        """

        pass


class NoopInstruction(Instruction):
    """
    No operation instruction.
    """

    pass


class MInstructionType(enum.Flag):
    """
    Type of Mindustry instruction.
    """

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
    """
    Mindustry instruction.
    """

    type: MInstructionType
    params: list[str]

    _native_name: str

    __match_args__ = ("type", "params")

    def __init__(self, type_: MInstructionType, params: list[str | int | float | Value]):
        self.type = type_

        # convert all parameters to strings
        self.params = list(map(str, params))

        if (native_name := self._get_native_name()).split(".")[0] not in Natives.NATIVES_PARAM_COUNT or \
                native_name not in Natives.ALL_NATIVES:

            InternalError.undefined_function(native_name)

        # check parameter count
        while len(self.params) < Natives.NATIVES_PARAM_COUNT[native_name.split(".")[0]]:
            self.params.append("_")

        self._native_name = native_name

    def __str__(self):
        return f"{self.type.name.lower()} {' '.join(map(str, self.params))}"

    def __repr__(self):
        return f"MInstruction({self.type}, {self.params})"

    def copy(self):
        return MInstruction(self.type, self.params.copy())

    def _params_no_subcommand(self):
        """
        Returns:
            This instruction's parameters without the subcommand configuration.
        """

        if "." in self._native_name:
            if self.type == MInstructionType.SENSOR:
                return self.params[:-1]

            return self.params[1:]

        return self.params

    def inputs(self) -> list[str]:
        return [self._params_no_subcommand()[i] for i, param in enumerate(Natives.ALL_NATIVES[self._native_name])
                if param[0] == Param.INPUT]

    def outputs(self) -> list[str]:
        return [self._params_no_subcommand()[i] for i, param in enumerate(Natives.ALL_NATIVES[self._native_name])
                if param[0] == Param.OUTPUT]

    def _get_native_name(self) -> str:
        if self.type in MInstructionType.DRAW | MInstructionType.CONTROL | MInstructionType.LOOKUP | \
                MInstructionType.SENSOR | MInstructionType.UCONTROL | MInstructionType.ULOCATE:

            return self.type.name.lower() + "." + (self.params[-1][1:] if self.type == MInstructionType.SENSOR
                                                     else self.params[0])

        return self.type.name.lower()

    def is_branching(self) -> bool:
        return self.type in MInstructionType.END | MInstructionType.JUMP

    def param_replace(self, from_: str, to: str):
        self.params = [param.replace(from_, to) for param in self.params]


class MppInstructionLabel(Instruction):
    """
    Label instruction.
    """

    name: str

    def __init__(self, name: str):
        self.name = str(name)

    def __str__(self):
        return f"{self.name}:"

    def __repr__(self):
        return f"MppInstructionLabel('{self.name}')"

    def copy(self):
        return MppInstructionLabel(self.name)


class MppInstructionJump(Instruction):
    """
    Jump instruction.
    """

    label: str

    def __init__(self, label: str):
        self.label = str(label)

    def __str__(self):
        return f"jump {self.label} always _ _"

    def __repr__(self):
        return f"MppInstructionJump('{self.label}')"

    def copy(self):
        return MppInstructionJump(self.label)


class MppInstructionOJump(Instruction):
    """
    Conditional jump instruction.
    """

    label: str
    op1: str
    op: str
    op2: str

    def __init__(self, label: str, op1: str | Value, op: str, op2: str | Value):
        self.label = str(label)
        self.op1 = str(op1)
        self.op = str(op)
        self.op2 = str(op2)

    def __str__(self):
        return f"jump {self.label} {self.op} {self.op1} {self.op2}"

    def __repr__(self):
        return f"MppInstructionOJump('{self.label}', '{self.op1}', '{self.op}', '{self.op2}')"

    def copy(self):
        return MppInstructionOJump(self.label, self.op1, self.op, self.op2)

    def inputs(self) -> list[str]:
        return [self.op1, self.op2]

    def param_replace(self, from_: str, to: str):
        self.op1 = self.op1.replace(from_, to)
        self.op2 = self.op2.replace(from_, to)


class Instructions:
    """
    A list of instructions.
    """

    def __init__(self, ins: list[Instruction] | None = None):
        self.ins = [] if ins is None else ins

    def __add__(self, other):
        """
        Join this list with an instruction or instructions.

        Args:
            other (Instruction | Instructions): The instruction or instructions to join.

        Returns:
            The joined instructions.
        """

        if isinstance(other, Instruction):
            return Instructions(self.ins + [other])
        elif isinstance(other, Instructions):
            return Instructions(self.ins + other.ins)

    def __iadd__(self, other) -> 'Instructions':
        """
        Append an instruction or instructions to this list.

        Args:
            other (Instruction | Instructions): The instruction or instructions to be appended.

        Returns:
            This list.
        """

        if isinstance(other, Instruction):
            self.ins.append(other)
        elif isinstance(other, Instructions):
            self.ins += other.ins

        return self

    def iter(self) -> list[Instruction]:
        """
        Create a list of all instructions in this list.

        Returns:
            A list of all instructions in this list.
        """

        return self.ins

    def __len__(self) -> int:
        return len(self.ins)

    def __getitem__(self, key: int):
        return self.ins[key]

    def __setitem__(self, key: int, value: Instruction):
        self.ins[key] = value

    def copy(self):
        return Instructions([ins.copy() for ins in self.ins])

    def param_replace(self, from_: str, to: str):
        """
        Replaces parameter names.

        Args:
            from_: Which names to replace.
            to: What to replace them with.
        """

        for ins in self.ins:
            ins.param_replace(from_, to)
