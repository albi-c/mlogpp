from ..util import Position
from ..values import *
from ..generator import Gen
from ..instruction import *
from .. import enums
from .. import instruction


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

    def gen(self):
        """
        Generate the node.

        Returns:
            The generated code.
        """

        raise NotImplementedError


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

    def gen(self):
        for node in self.code:
            node.gen()


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

    def gen(self):
        if self.op == "=":
            if "." in self.var and (spl := self.var.split(".", 1))[1] in enums.CONTROLLABLE:
                Gen.emit(
                    InstructionControl(spl[1], spl[0], self.value, 0, 0, 0)
                )

            else:
                Gen.emit(
                    InstructionSet(self.var, self.value)
                )

            return

        Gen.emit(
            InstructionOp(AssignmentNode.OPERATORS[self.op], self.var, self.var, self.value)
        )


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

    def gen(self):
        Gen.emit(
            InstructionWrite(self.value, self.cell, self.index)
        )


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

    def gen(self):
        Gen.emit(
            InstructionRead(self.value, self.cell, self.index)
        )


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

    def gen(self):
        Gen.emit(
            InstructionOp(BinaryOpNode.OPERATORS[self.op], self.result, self.left, self.right)
        )


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

    def gen(self):
        match self.op:
            case "-":
                Gen.emit(
                    InstructionOp("sub", self.result, 0, self.value)
                )
            case "!":
                Gen.emit(
                    InstructionOp("equal", self.result, self.value, 0)
                )
            case "~":
                Gen.emit(
                    InstructionOp("not", self.result, self.value, 0)
                )


class LabelNode(Node):
    """
    Label.
    """

    name: str

    def __init__(self, pos: Position, name: str):
        super().__init__(pos)

        self.name = name

    def gen(self):
        Gen.emit(
            Label(self.name)
        )


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

    def gen(self):
        Gen.emit(
            InstructionJump(self.label, *self.condition)
        )


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

    def __str__(self):
        return f"{self.name}({', '.join(map(str, self.params))})"

    def gen(self):
        ins = instruction.INSTRUCTIONS[self.name]
        Gen.emit(
            ins(*self.params, *([0] * (ins.num_params() - len(self.params))))
        )
