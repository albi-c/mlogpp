import types

from .util import Position
from .instruction import *
from .value import *
from .generator import Gen
from .scope import Scopes
from .error import gen_error, GenErrorType, Error


class Node:
    """
    base node class
    """

    pos: Position

    def __init__(self, pos: Position):
        self.pos = pos

    def get_pos(self) -> Position:
        return self.pos

    def __str__(self):
        return "NODE"

    def generate(self) -> Instruction | Instructions:
        return Instructions()

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return Instructions(), NullValue()

    def set(self) -> tuple[Instruction | Instructions, Value]:
        return Instructions(), NullValue()


class CodeBlockNode(Node):
    """
    block of code
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

        Scopes.push()

        for node in self.code:
            ins += node.generate()

        Scopes.pop()

        return ins


class DeclarationNode(Node):
    """
    variable declaration node
    """

    var: VariableValue
    value: Node | None

    def __init__(self, pos: Position, var: VariableValue, value: Node | None):
        super().__init__(pos)

        self.var = var
        self.value = value

    def __str__(self):
        return f"{self.var.type.name} {self.var.name} = {str(self.value)}"

    def generate(self) -> Instruction | Instructions:
        Scopes.add(self.var)

        if self.value is not None:
            value_code, value = self.value.get()

            if value.type != self.var.type:
                Error.incompatible_types(self, value.type, self.var.type)

            return value_code + MInstruction(MInstructionType.SET, [self.var.name, value])

        return Instructions()


class AssignmentNode(Node):
    """
    variable assignment node
    """

    var: str
    op: str
    value: Node

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

    def __init__(self, pos: Position, var: str, op: str, value: Node):
        super().__init__(pos)

        self.var = var
        self.op = op
        self.value = value

    def __str__(self):
        return f"{self.var} {self.op} {self.value}"

    def generate(self) -> Instruction | Instructions:
        if (var := Scopes.get(self.var)) is not None:
            value_code, value = self.value.get()

            if self.op == "=":
                return value_code + MInstruction(MInstructionType.SET, [var, value])
            else:
                if var.type != Type.NUM:
                    Error.incompatible_types(self, var.type, Type.NUM)
                if value.type != Type.NUM:
                    Error.incompatible_types(self, value.type, Type.NUM)

                return value_code + MInstruction(MInstructionType.OP, [self.OPERATORS[self.op], var, var, value])\

        raise RuntimeError()


class IndexedAssignmentNode(AssignmentNode):
    """
    indexed variable assignment node
    """

    index: Node

    def __init__(self, pos: Position, var: str, index: Node, op: str, value: Node):
        super().__init__(pos, var, op, value)

        self.index = index

    def __str__(self):
        return f"{self.var}[{self.index}] {self.op} {self.value}"

    def generate(self) -> Instruction | Instructions:
        if (var := Scopes.get(self.var)) is not None:
            value_code, value = self.value.get()
            index_code, index = self.index.get()

            if var.type != Type.NUM:
                Error.incompatible_types(self, var.type, Type.NUM)
            if value.type != Type.NUM:
                Error.incompatible_types(self, value.type, Type.NUM)
            if index.type != Type.NUM:
                Error.incompatible_types(self, index.type, Type.NUM)

            if self.op == "=":
                return value_code + index_code + MInstruction(MInstructionType.WRITE, [value, var, index])
            else:
                tmp = Gen.temp_var(Type.NUM)
                return index_code + MInstruction(MInstructionType.READ, [tmp, var, index]) + value_code + \
                       MInstruction(MInstructionType.OP, [AssignmentNode.OPERATORS[self.op], tmp, tmp, value]) + \
                       MInstruction(MInstructionType.WRITE, [tmp, var, index])

        raise RuntimeError()


class BinaryOpNode(Node):
    """
    binary operator node
    """

    left: Node
    right: list[tuple[str, Node]] | None

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

    def __init__(self, pos: Position, left: Node, right: list[tuple[str, Node]] | None):
        super().__init__(pos)

        self.left = left
        self.right = right

    def __str__(self):
        string = str(self.left)
        for op, node in self.right:
            string += " " + op + f" {str(node)}"
        return string

    def get(self) -> tuple[Instruction | Instructions, Value]:
        code, value = self.left.get()

        if value.type != Type.NUM:
            Error.incompatible_types(self, value.type, Type.NUM)

        if self.right is not None and len(self.right) > 0:
            tmpv = Gen.temp_var(Type.NUM, value)
            if tmpv != value:
                code += MInstruction(MInstructionType.SET, [tmpv, value])

            for op, node in self.right:
                value_code, value = node.get()

                if value.type != Type.NUM:
                    Error.incompatible_types(self, value.type, Type.NUM)

                code += value_code + MInstruction(MInstructionType.OP, [op, tmpv, tmpv, value])

            return code, tmpv

        return code, value


class UnaryOpNode(Node):
    """
    unary operator node
    """

    op: str
    value: Node

    def __init__(self, pos: Position, op: str, value: Node):
        super().__init__(pos)

        self.op = op
        self.value = value

    def __str__(self):
        return f"{self.op}{str(self.value)}"

    def get(self) -> tuple[Instruction | Instructions, Value]:
        code, value = self.value.get()

        if value.type != Type.NUM:
            Error.incompatible_types(self, value.type, Type.NUM)

        tmpv = Gen.temp_var(Type.NUM, value)

        match self.op:
            case "-":
                code += MInstruction(MInstructionType.OP, ["sub", tmpv, 0, tmpv])
            case "!":
                code += MInstruction(MInstructionType.OP, ["notEqual", tmpv, tmpv, "true"])
            case "~":
                code += MInstruction(MInstructionType.OP, ["not", tmpv, tmpv, "_"])

        return code, value


class CallNode(Node):
    """
    function call node
    """

    name: str
    params: list[Node]

    return_value: Value

    NATIVES = {
        "read": {
            "params": 3,
            inputs: {
                1: Type.BUILDING,
                2: Type.NUM
            },
            "outputs": {
                0: Type.NUM
            }
        },
        "write": {
            "params": 3,
            "inputs": {
                0: Type.NUM,
                1: Type.BUILDING,
                2: Type.NUM
            }
        },
        "draw": {
            "params": 7,
            "subcommands": True
        },
        "print": {
            "params": 1,
            "inputs": {
                0: Type.ANY
            }
        },
        "drawflush": {
            "params": 1,
            "inputs": {
                0: Type.BUILDING
            }
        },
        "printflush": {
            "params": 1,
            "inputs": {
                0: Type.BUILDING
            }
        },
        "getlink": {
            "params": 2,
            "inputs": {
                1: Type.NUM
            },
            "outputs": {
                0: Type.BUILDING
            }
        },
        "control": {
            "params": 6,
            "subcommands": True
        },
        "radar": {
            "params": 7,
            "inputs": {
                4: Type.BUILDING,
                5: Type.NUM
            },
            "outputs": {
                6: Type.UNIT
            }
        },
        "sensor": {
            "params": 3,
            "subcommands": True
        },
        "wait": {
            "params": 1,
            "inputs": {
                0: Type.NUM
            }
        },
        "packcolor": {
            "params": 5,
            "inputs": {
                1: Type.NUM,
                2: Type.NUM,
                3: Type.NUM,
                4: Type.NUM
            },
            "outputs": {
                0: Type.NUM
            }
        },
        "ubind": {
            "params": 1,
            "inputs": {
                0: Type.UNIT_TYPE
            }
        },
        "uradar": {
            "params": 7,
            "inputs": {
                5: Type.NUM
            },
            "outputs": {
                6: Type.UNIT
            },
            "empty": {
                4
            }
        }
    }

    # default input type - number, all inputs
    SUBCOMMANDS_DRAW = {
        "clear": 3,
        "color": 4,
        "col": 1,
        "stroke": 1,
        "line": 4,
        "rect": 4,
        "lineRect": 4,
        "poly": 5,
        "linePoly": 5,
        "triangle": 6,

        "image": {
            "params": 5,
            "inputs": {
                2: Type.ITEM_TYPE
            }
        }
    }

    # default first parameter building
    SUBCOMMANDS_CONTROL = {
        "enabled": {
            "params": 2,
            "inputs": {
                1: Type.NUM
            }
        },
        "shoot": {
            "params": 4,
            "inputs": {
                1: Type.NUM,
                2: Type.NUM,
                3: Type.NUM
            }
        },
        "shootp": {
            "params": 2,
            "inputs": {
                1: Type.UNIT,
                2: Type.NUM
            }
        },
        "config": {
            "params": 1,
            "inputs": {
                1: Type.NUM
            }
        },
        "color": {
            "params": 1,
            "inputs": {
                1: Type.NUM
            }
        }
    }

    # default output type - number
    SUBCOMMANDS_SENSOR = {
        "type": Type.BUILDING_TYPE,
        "controlled": Type.OTHER,
        "controller": Type.BUILDING | Type.UNIT
    }

    def __init__(self, pos: Position, name: str, params: list[Node]):
        super().__init__(pos)

        self.name = name
        self.params = params

    def __str__(self):
        return f"{self.name}({', '.join(map(str, self.params))})"

    def generate(self) -> Instruction | Instructions:
        pass

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return self.generate(), self.return_value


class ValueNode(Node):
    """
    value node
    """

    def __init__(self, pos: Position, value):
        super().__init__(pos)

        self.value = value

    def __str__(self):
        return str(self.value)


class StringValueNode(ValueNode):
    """
    string value node
    """

    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return Instructions(), StringValue(self.value)


class NumberValueNode(ValueNode):
    """
    number value node
    """

    value: int | float

    def __init__(self, pos: Position, value: int | float):
        super().__init__(pos, value)

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return Instructions(), NumberValue(self.value)


class VariableValueNode(ValueNode):
    """
    variable value node
    """

    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def get(self) -> tuple[Instruction | Instructions, Value]:
        if (var := Scopes.get(self.value)) is not None:
            return Instructions(), var

        raise RuntimeError()


class IndexedValueNode(ValueNode):
    """
    indexed variable value node
    """

    value: str
    index: Node

    def __init__(self, pos: Position, value: str, index: Node):
        super().__init__(pos, value)

        self.index = index

    def __str__(self):
        return f"{self.value}[{self.index}]"


class ReturnNode(Node):
    """
    return from function node
    """

    func: str
    value: Node | None

    def __init__(self, pos: Position, func: str, value: Node | None):
        super().__init__(pos)

        self.func = func
        self.value = value


class BreakNode(Node):
    """
    break loop node
    """

    loop: str

    def __init__(self, pos: Position, loop: str):
        super().__init__(pos)

        self.loop = loop


class ContinueNode(Node):
    """
    continue loop node
    """

    loop: str

    def __init__(self, pos: Position, loop: str):
        super().__init__(pos)

        self.loop = loop


class EndNode(Node):
    """
    end program node
    """

    def __init__(self, pos: Position):
        super().__init__(pos)


class IfNode(Node):
    """
    if conditional node
    """

    cond: Node
    code: CodeBlockNode
    else_code: CodeBlockNode | None

    def __init__(self, pos: Position, cond: Node, code: CodeBlockNode, else_code: CodeBlockNode | None):
        super().__init__(pos)

        self.cond = cond
        self.code = code
        self.else_code = else_code


class LoopNode(Node):
    """
    loop node
    """

    def __init__(self, pos: Position):
        super().__init__(pos)


class WhileNode(LoopNode):
    """
    while loop node
    """

    name: str
    cond: Node
    code: CodeBlockNode

    def __init__(self, pos: Position, name: str, cond: Node, code: CodeBlockNode):
        super().__init__(pos)

        self.name = name
        self.cond = cond
        self.code = code


class ForNode(LoopNode):
    """
    for loop node
    """

    name: str
    init: Node
    cond: Node
    action: Node
    code: CodeBlockNode

    def __init__(self, pos: Position, name: str, init: Node, cond: Node, action: Node, code: CodeBlockNode):
        super().__init__(pos)

        self.name = name
        self.init = init
        self.cond = cond
        self.action = action
        self.code = code


class RangeNode(LoopNode):
    """
    range loop node
    """

    name: str
    var: str
    until: Node
    code: CodeBlockNode

    def __init__(self, pos: Position, name: str, var: str, until: Node, code: CodeBlockNode):
        super().__init__(pos)

        self.name = name
        self.var = var
        self.until = until
        self.code = code


class FunctionNode(Node):
    """
    function definition node
    """

    name: str
    params: list[str]
    code: CodeBlockNode

    def __init__(self, pos: Position, name: str, params: list[str], code: CodeBlockNode):
        super().__init__(pos)

        self.name = name
        self.params = params
        self.code = code

    def generate(self) -> Instruction | Instructions:
        # TODO: function definition generation
        return Instructions()
