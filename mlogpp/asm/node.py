from ..util import Position
from ..instruction import *
from ..value import *
from .. import constants


class Node:
    """
    Base node class.
    """

    pos: Position

    def __init__(self, pos: Position):
        self.pos = pos

    def get_pos(self) -> Position:
        """
        Get position of the node.

        Returns:
            Position of the node.
        """

        return self.pos

    def __str__(self):
        """
        Convert the node to a string, debug only.

        Returns:
            A string, similar to the unparsed mlog++ code.
        """

        return "NODE"

    def generate(self) -> Instruction | Instructions:
        """
        Generate the node.

        Returns:
            The generated code.
        """

        return Instructions()


class CodeBlockNode(Node):
    """
    Block of code.
    """

    code: list[Node]

    def __init__(self, code: list[Node]):
        super().__init__(Position(0, 0, 0, "", ""))

        self.code = code

    def __str__(self):
        string = "{\n"
        for node in self.code:
            string += str(node) + "\n"
        return string + "}"

    def generate(self) -> Instruction | Instructions:
        ins = Instructions()

        for node in self.code:
            ins += node.generate()

        return ins


class AssignmentNode(Node):
    """
    Variable assignment.
    """

    var: str
    op: str
    value: Value

    # mlog++ to mindustry logic operator map
    OPERATORS = {
        "+=": "add",
        "-=": "sub",
        "%=": "mod",
        "&=": "and",
        "|=": "or",
        "^=": "xor",
        "*=": "mul",
        "/=": "div",
        "**=": "pow",
        "//=": "idiv",
        "<<": "shl",
        ">>": "shr"
    }

    def __init__(self, pos: Position, var: str, op: str, value: Value):
        super().__init__(pos)

        self.var = var
        self.op = op
        self.value = value

    def __str__(self):
        return f"{self.var} {self.op} {self.value}"

    def generate(self) -> Instruction | Instructions:
        if self.op == "=":
            if "." in self.var and (spl := self.var.split(".", 1))[1] in constants.CONTROLLABLE:
                return MInstruction(MInstructionType.CONTROL, [
                    spl[1],
                    spl[0],
                    self.value,
                    "_", "_", "_"
                ])

            else:
                return MInstruction(MInstructionType.SET, [self.var, self.value])

        return MInstruction(MInstructionType.OP, [AssignmentNode.OPERATORS[self.op], self.var, self.var, self.value])


class CellWriteNode(Node):
    """
    Memory cell write.
    """

    cell: str
    index: Value
    value: Value

    def __init__(self, pos: Position, cell: str, index: Value, value: Value):
        super().__init__(pos)

        self.cell = cell
        self.index = index
        self.value = value

    def generate(self) -> Instruction | Instructions:
        return MInstruction(MInstructionType.WRITE, [self.value, self.cell, self.index])


class CellReadNode(Node):
    """
    Memory cell read.
    """

    cell: str
    index: Value
    value: str

    def __init__(self, pos: Position, cell: str, index: Value, value: str):
        super().__init__(pos)

        self.cell = cell
        self.index = index
        self.value = value

    def generate(self) -> Instruction | Instructions:
        return MInstruction(MInstructionType.READ, [self.value, self.cell, self.index])


class BinaryOpNode(Node):
    """
    Binary operator.
    """

    result: str
    left: Value
    op: str
    right: Value

    # mlog++ to mindustry logic operator map
    OPERATORS = {
        "+": "add",
        "-": "sub",
        "*": "mul",
        "/": "div",
        "//": "idiv",
        "%": "mod",
        "**": "pow",
        "==": "equal",
        "!=": "notEqual",
        "&&": "land",
        "||": "or",
        "<": "lessThan",
        "<=": "lessThanEq",
        ">": "greaterThan",
        ">=": "greaterThanEq",
        "===": "strictEqual",
        "<<": "shl",
        ">>": "shr",
        "|": "or",
        "&": "and",
        "^": "xor"
    }

    # equality check operators
    EQUALITY = {
        "==",
        "!=",
        "==="
    }

    def __init__(self, pos: Position, result: str, left: Value, op: str, right: Value):
        super().__init__(pos)

        self.result = result
        self.left = left
        self.op = op
        self.right = right

    def __str__(self):
        return f"{self.left} {self.op} {self.right}"

    def generate(self) -> Instruction | Instructions:
        return MInstruction(MInstructionType.OP, [BinaryOpNode.OPERATORS[self.op], self.result, self.left, self.right])


class UnaryOpNode(Node):
    """
    Unary operator.
    """

    result: str
    op: str
    value: Value

    def __init__(self, pos: Position, result: str, op: str, value: Value):
        super().__init__(pos)

        self.result = result
        self.op = op
        self.value = value

    def __str__(self):
        return f"{self.op}{str(self.value)}"

    def generate(self) -> Instruction | Instructions:
        match self.op:
            case "-":
                return MInstruction(MInstructionType.OP, ["sub", self.result, NumberValue(0), self.value])
            case "!":
                return MInstruction(MInstructionType.OP, ["equal", self.result, self.value, NumberValue(0)])
            case "~":
                return MInstruction(MInstructionType.OP, ["not", self.result, self.value, "_"])


class LabelNode(Node):
    """
    Label.
    """

    name: str

    def __init__(self, pos: Position, name: str):
        super().__init__(pos)

        self.name = name

    def generate(self) -> Instruction | Instructions:
        return MppInstructionLabel(self.name)


class JumpNode(Node):
    """
    Jump.
    """

    CONDITIONS = {
        "==": "equal",
        "!=": "notEqual",
        "<": "lessThan",
        "<=": "lessThanEq",
        ">": "greaterThan",
        ">=": "greaterThanEq",
        "===": "strictEqual"
    }

    label: str
    condition: list[str | Value]

    def __init__(self, pos: Position, label: str, condition: tuple[str, Value, Value]):
        super().__init__(pos)

        self.label = label
        self.condition = [JumpNode.CONDITIONS.get(condition[0], condition[0]), condition[1], condition[2]]

    def generate(self) -> Instruction | Instructions:
        return MInstruction(MInstructionType.JUMP, [self.label] + self.condition)


class CallNode(Node):
    """
    Function call.
    """

    name: str
    params: list[Value]

    def __init__(self, pos: Position, name: str, params: list[Value]):
        super().__init__(pos)

        self.name = name
        self.params = params

    def generate(self) -> Instruction | Instructions:
        return MInstruction(MInstructionType[self.name.upper()], self.params)
