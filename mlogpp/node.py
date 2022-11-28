import types

from .util import Position
from .instruction import *
from .value import *
from .generator import Gen
from .scope import Scope, Scopes
from .function import Function
from .functions import Natives, Param
from .error import Error
from . import constants


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

    def get(self) -> tuple[Instruction | Instructions, Value]:
        """
        Get the node's value and code to obtain it.

        Returns:
            A tuple containing the code to obtain the value and the value.
        """

        return Instructions(), NullValue()


class CodeBlockNode(Node):
    """
    Block of code.
    """

    code: list[Node]
    name: str | None

    def __init__(self, code: list[Node], name: str | None):
        super().__init__(Position(0, 0, 0, "", ""))

        self.code = code
        self.name = name

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

    def push_scope(self) -> None:
        """
        Push this node's scope to the scope stack.
        """

        Scopes.push(self.name)

    @staticmethod
    def pop_scope() -> None:
        """
        Pop this node's scope from the scope stack.
        """

        Scopes.pop()


class DeclarationNode(Node):
    """
    Variable declaration.
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
        self.var.name = Scopes.rename(self.var.name, True)

        # check if variable already exists
        if Scopes.get(self.var.name) is not None:
            Error.already_defined_var(self, self.var.name)

        Scopes.add(self.var)

        # assign a value to the variable
        if self.value is not None:
            value_code, value = self.value.get()

            # check if the value has a correct type
            if value.type not in self.var.type:
                Error.incompatible_types(self, value.type, self.var.type)

            return value_code + MInstruction(MInstructionType.SET, [self.var, value])

        return Instructions()


class AssignmentNode(Node):
    """
    Variable assignment.
    """

    var: str
    op: str
    value: Node

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

    def __init__(self, pos: Position, var: str, op: str, value: Node):
        super().__init__(pos)

        self.var = var
        self.op = op
        self.value = value

    def __str__(self):
        return f"{self.var} {self.op} {self.value}"

    def generate(self) -> Instruction | Instructions:
        # rename only the first part of the variable if name contains an "."
        if "." in self.var:
            spl = self.var.split(".")
            self.var = Scopes.rename(spl[0]) + "." + spl[1]
        else:
            self.var = Scopes.rename(self.var)

        # check if the variable exists
        if isinstance(var := Scopes.get(self.var), VariableValue):
            # check if the variable is a constant
            if var.const:
                Error.write_to_const(self, self.var)

            value_code, value = self.value.get()

            if self.op == "=":
                # check if the variable being assigned to is of the same type as the value being used
                if value.type not in var.type:
                    Error.incompatible_types(self, value.type, var.type)

                return value_code + MInstruction(MInstructionType.SET, [var, value])
            else:
                # check if the variable being assigned to is a number for arithmetic operations
                if var.type not in Type.NUM:
                    Error.incompatible_types(self, var.type, Type.NUM)
                # check if the value being used is a number for arithmetic operations
                if value.type not in Type.NUM:
                    Error.incompatible_types(self, value.type, Type.NUM)

                return value_code + MInstruction(MInstructionType.OP, [self.OPERATORS[self.op], var, var, value])

        # if variable doesn't exist, check if it is a control command
        if self.op == "=" and "." in self.var and (spl := self.var.split("."))[1] in constants.CONTROLLABLE:
            value_code, value = self.value.get()

            # check if the value used is a number
            if value.type != Type.NUM:
                Error.incompatible_types(self, value.type, Type.NUM)

            # check if the block being controlled exists
            if not isinstance(var := Scopes.get(spl[0]), VariableValue):
                Error.undefined_variable(self, spl[0])

            # check if the variable is a block
            if var.type != Type.BLOCK:
                Error.incompatible_types(self, var.type, Type.BLOCK)

            return value_code + MInstruction(MInstructionType.CONTROL, [
                spl[1],
                var,
                value,
                "_", "_", "_"
            ])

        Error.undefined_variable(self, self.var)


class IndexedAssignmentNode(AssignmentNode):
    """
    Memory cell indexed assignment.
    """

    index: Node

    def __init__(self, pos: Position, var: str, index: Node, op: str, value: Node):
        super().__init__(pos, var, op, value)

        self.index = index

    def __str__(self):
        return f"{self.var}[{self.index}] {self.op} {self.value}"

    def generate(self) -> Instruction | Instructions:
        # check if the variable exists
        if (var := Scopes.get(self.var)) is not None:
            value_code, value = self.value.get()
            index_code, index = self.index.get()

            # check if the memory cell variable is a block
            if var.type not in Type.BLOCK:
                Error.incompatible_types(self, var.type, Type.NUM)
            # check if the value being used is a number
            if value.type not in Type.NUM:
                Error.incompatible_types(self, value.type, Type.NUM)
            # check if the index is a number
            if index.type not in Type.NUM:
                Error.incompatible_types(self, index.type, Type.NUM)

            if self.op == "=":
                return value_code + index_code + MInstruction(MInstructionType.WRITE, [value, var, index])
            else:
                # a temporary variable for the arithmetic operation
                tmp = Gen.temp_var(Type.NUM)

                return index_code + MInstruction(MInstructionType.READ, [tmp, var, index]) + value_code + \
                       MInstruction(MInstructionType.OP, [AssignmentNode.OPERATORS[self.op], tmp, tmp, value]) + \
                       MInstruction(MInstructionType.WRITE, [tmp, var, index])

        Error.undefined_variable(self, self.var)


class BinaryOpNode(Node):
    """
    binary operator node
    """

    left: Node
    right: list[tuple[str, Node]] | None

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

        # check if the value is a number for arithmetic operations
        if value.type not in Type.NUM and len(self.right) > 0:
            for op, _ in self.right:
                if op not in BinaryOpNode.EQUALITY:
                    Error.incompatible_types(self, value.type, Type.NUM)

        if self.right is not None and len(self.right) > 0:
            current_value = value

            for op, node in self.right:
                value_code, value = node.get()

                # check if the right side value of the arithmetic operation has the right type
                if value.type not in Type.NUM and op not in BinaryOpNode.EQUALITY:
                    Error.incompatible_types(self, value.type, Type.NUM)

                # temporary variable for the output of the operation
                tmpv = Gen.temp_var(Type.NUM)

                code += value_code + MInstruction(MInstructionType.OP, [BinaryOpNode.OPERATORS[op], tmpv, current_value, value])

                current_value = tmpv

            return code, current_value

        return code, value


class UnaryOpNode(Node):
    """
    Unary operator.
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

        # check if the value is a number
        if value.type not in Type.NUM:
            Error.incompatible_types(self, value.type, Type.NUM)

        tmpv = Gen.temp_var(Type.NUM)

        match self.op:
            case "-":
                code += MInstruction(MInstructionType.OP, ["sub", tmpv, NumberValue(0), value])
            case "!":
                code += MInstruction(MInstructionType.OP, ["equal", tmpv, value, NumberValue(0)])
            case "~":
                code += MInstruction(MInstructionType.OP, ["not", tmpv, value, "_"])

        return code, tmpv


class CallNode(Node):
    """
    Function call.
    """

    name: str
    params: list[Node]

    return_value: Value

    def __init__(self, pos: Position, name: str, params: list[Node]):
        super().__init__(pos)

        self.name = name
        self.params = params

        self.return_value = NullValue()

    def generate(self) -> Instruction | Instructions:
        code = Instructions()

        # check if the function is defined
        if not isinstance(fun := Scopes.get(self.name), Function):
            Error.undefined_function(self, self.name)

        # check if the parameter count is correct
        if len(self.params) != len(fun.params):
            Error.invalid_arg_count(self, len(self.params), len(fun.params))

        # save the return value for later use
        if fun.return_type != Type.NULL:
            self.return_value = VariableValue(fun.return_type, f"__f_{self.name}_retv")

        # generate every parameter
        for i, param in enumerate(self.params):
            param_code, param_value = param.get()

            # check if the parameter is of the correct type
            if param_value.type != fun.params[i][1]:
                Error.incompatible_types(self, param_value.type, fun.params[i][1])

            code += param_code
            code += MInstruction(MInstructionType.SET, [
                VariableValue(fun.params[i][1], Scope(self.name).rename(fun.params[i][0])),
                param_value
            ])

        code += MInstruction(MInstructionType.OP, [
            "add",
            VariableValue(Type.NUM, f"__f_{self.name}_ret"),
            VariableValue(Type.NUM, "@counter"),
            NumberValue(1)
        ])
        code += MppInstructionJump(f"__f_{self.name}")

        return code

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return self.generate(), self.return_value


class NativeCallNode(Node):
    """
    Native function call.
    """

    name: str
    params: list[Node | str]

    return_value: Value

    NATIVES = Natives.NATIVES
    NATIVES_RETURN_POS = Natives.NATIVES_RETURN_POS
    BUILTINS = Natives.BUILTINS

    def __init__(self, pos: Position, name: str, params: list[Node | str]):
        super().__init__(pos)

        self.name = name
        self.params = params

        self.return_value = NullValue()

    def __str__(self):
        return f"{self.name}({', '.join(map(str, self.params))})"

    def generate(self) -> Instruction | Instructions:
        if self.name in NativeCallNode.NATIVES:
            return self.generate_native()
        elif self.name in NativeCallNode.BUILTINS:
            return self.generate_builtin()

        Error.undefined_function(self, self.name)

    def generate_native(self) -> Instruction | Instructions:
        # check if the function is native
        if (nat := NativeCallNode.NATIVES.get(self.name)) is None:
            Error.undefined_function(self, self.name)

        # check the number of parameters
        if len(self.params) != len(nat):
            Error.invalid_arg_count(self, len(self.params), len(nat))

        code = Instructions()

        params = []

        # generate the parameters
        for i, param in enumerate(self.params):
            match nat[i][0]:
                # a configuration string
                case Param.CONFIG:
                    if isinstance(param, str):
                        params.append(param)

                # an unused parameter
                case Param.UNUSED:
                    params.append("_")

                # an input parameter
                case Param.INPUT:
                    param_code, param_value = param.get()

                    # check if the parameter's type is correct
                    if param_value.type not in nat[i][1]:
                        Error.incompatible_types(self, param_value.type, nat[i][1])

                    code += param_code
                    params.append(param_value)

                # an output parameter
                case Param.OUTPUT:
                    if i == NativeCallNode.NATIVES_RETURN_POS.get(self.name):
                        # the returned value
                        value = Gen.temp_var(nat[i][1])
                        self.return_value = value
                        params.append(value)

                    else:
                        param = Scopes.rename(param, True)

                        # declare the output variable if it doesn't exist yet
                        if (var := Scopes.get(param)) is None:
                            var = VariableValue(nat[i][1], param)
                            Scopes.add(var)

                        # check if the output variable is already defined as a function
                        elif isinstance(var, Function):
                            Error.already_defined_var(self, param)

                        # check if the output variable is of the correct type
                        elif var.type != nat[i][1]:
                            Error.incompatible_types(self, var.type, nat[i][1])

                        params.append(var)

        # subcall
        if "." in self.name:
            # sensor has its subcall at the end
            if self.name == "sensor":
                params.append("@" + self.name.split(".")[1])

            # others have the subcall at the start
            else:
                params = [self.name.split(".")[1]] + params

        code += MInstruction(MInstructionType[self.name.split(".")[0].upper()], params)

        return code

    def generate_builtin(self) -> Instruction | Instructions:
        # check if the function is builtin
        if (nat := NativeCallNode.BUILTINS.get(self.name)) is None:
            Error.undefined_function(self, self.name)

        # check the parameter count
        if len(self.params) != nat:
            Error.invalid_arg_count(self, len(self.params), nat)

        code = Instructions()

        params = []

        # generate the parameters
        for param in self.params:
            param_code, param_value = param.get()

            # check if the parameter is a number
            if param_value.type != Type.NUM:
                Error.incompatible_types(self, param_value.type, Type.NUM)

            code += param_code
            params.append(param_value)

        out = Gen.temp_var(Type.NUM)

        code += MInstruction(MInstructionType.OP, [
            self.name,
            out,
            *params
        ] + ["_"] * (2 - len(params)))

        self.return_value = out

        return code

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return self.generate(), self.return_value


class ValueNode(Node):
    """
    Value.
    """

    def __init__(self, pos: Position, value):
        super().__init__(pos)

        self.value = value

    def __str__(self):
        return str(self.value)


class StringValueNode(ValueNode):
    """
    String value.
    """

    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return Instructions(), StringValue(self.value)


class NumberValueNode(ValueNode):
    """
    Number value.
    """

    value: int | float

    def __init__(self, pos: Position, value: int | float):
        super().__init__(pos, value)

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return Instructions(), NumberValue(self.value)


class ContentValueNode(ValueNode):
    """
    Content value.
    """

    value: str
    type: Type

    def __init__(self, pos: Position, value: str, type_: Type):
        super().__init__(pos, value)

        self.type = type_

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return Instructions(), VariableValue(self.type, self.value)


class BlockValueNode(ValueNode):
    """
    Linked block value.
    """

    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def get(self) -> tuple[Instruction | Instructions, Value]:
        return Instructions(), BlockValue(self.value)


class VariableValueNode(ValueNode):
    """
    Variable value.
    """

    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def get(self) -> tuple[Instruction | Instructions, Value]:
        # rename only the first part of the variable if it contains a "."
        if "." in self.value:
            spl = self.value.split(".")
            self.value = Scopes.rename(spl[0]) + "." + spl[1]
        else:
            self.value = Scopes.rename(self.value)

        # check if it is a plain variable
        if isinstance(var := Scopes.get(self.value), VariableValue):
            return Instructions(), var

        # check if it is a property access
        if "." in self.value and (spl := self.value.split("."))[1] in constants.SENSOR_READABLE:
            if isinstance(var := Scopes.get(spl[0]), VariableValue):
                # check if the variable is of the correct type
                if var.type not in Type.BLOCK | Type.UNIT:
                    Error.incompatible_types(self, var.type, Type.BLOCK)

                out = Gen.temp_var(constants.SENSOR_READABLE[spl[1]])

                return Instructions() + MInstruction(MInstructionType.SENSOR, [out, var, "@" + spl[1]]), out

        Error.undefined_variable(self, self.value)


class IndexedValueNode(ValueNode):
    """
    Memory cell indexed value.
    """

    value: str
    index: Node

    def __init__(self, pos: Position, value: str, index: Node):
        super().__init__(pos, value)

        self.index = index

    def __str__(self):
        return f"{self.value}[{self.index}]"

    def get(self) -> tuple[Instruction | Instructions, Value]:
        self.value = Scopes.rename(self.value)

        # check if the variable exists
        if not isinstance(var := Scopes.get(self.value), VariableValue):
            Error.undefined_variable(self, self.value)

        # check if the variable is a block
        if var.type != Type.BLOCK:
            Error.incompatible_types(self, var.type, Type.BLOCK)

        index_code, index = self.index.get()

        # check if the index is a number
        if index.type != Type.NUM:
            Error.incompatible_types(self, index.type, Type.NUM)

        out = Gen.temp_var(Type.NUM)

        return index_code + MInstruction(MInstructionType.READ, [out, var, index]), out


class ReturnNode(Node):
    """
    Return from a function.
    """

    func: str
    value: Node | None

    def __init__(self, pos: Position, func: str, value: Node | None):
        super().__init__(pos)

        self.func = func
        self.value = value

    def generate(self) -> Instruction | Instructions:
        # check if it returns a value
        if self.value is None:
            return Instructions() + MInstruction(MInstructionType.SET, [
                VariableValue(Type.NUM, "@counter"),
                VariableValue(Type.NUM, f"__f_{self.func}_ret")
            ])

        value_code, value = self.value.get()

        # check if the function returned from exists
        if not isinstance(fun := Scopes.get(self.func), Function):
            Error.undefined_function(self, self.name)

        # check if the returned value is of the correct type
        if value.type != fun.return_type:
            Error.incompatible_types(self, value.type, fun.return_type)

        return value_code + MInstruction(MInstructionType.SET, [
            VariableValue(value.type, f"__f_{self.func}_retv"),
            value
        ]) + MInstruction(MInstructionType.SET, [
            VariableValue(Type.NUM, "@counter"),
            VariableValue(Type.NUM, f"__f_{self.func}_ret")
        ])


class BreakNode(Node):
    """
    Break a loop.
    """

    loop: str

    def __init__(self, pos: Position, loop: str):
        super().__init__(pos)

        self.loop = loop

    def generate(self) -> Instruction | Instructions:
        return Instructions() + MppInstructionJump(f"{self.loop}_e")


class ContinueNode(Node):
    """
    Continue a loop.
    """

    loop: str

    def __init__(self, pos: Position, loop: str):
        super().__init__(pos)

        self.loop = loop

    def generate(self) -> Instruction | Instructions:
        return Instructions() + MppInstructionJump(f"{self.loop}_c")


class EndNode(Node):
    """
    End the program.
    """

    def __init__(self, pos: Position):
        super().__init__(pos)

    def generate(self) -> Instruction | Instructions:
        return Instructions() + MppInstructionJump("start")


class IfNode(Node):
    """
    If conditional.
    """

    cond: Node
    code: CodeBlockNode
    else_code: CodeBlockNode | None

    def __init__(self, pos: Position, cond: Node, code: CodeBlockNode, else_code: CodeBlockNode | None):
        super().__init__(pos)

        self.cond = cond
        self.code = code
        self.else_code = else_code

    def generate(self) -> Instruction | Instructions:
        self.code.push_scope()

        cond_code, cond = self.cond.get()

        code = self.code.generate()

        self.code.pop_scope()

        if self.else_code is not None:
            self.else_code.push_scope()
            else_code = self.else_code.generate()
            self.else_code.pop_scope()

            else_label = Gen.temp_lab()
            end_label = Gen.temp_lab()

            return cond_code + MppInstructionOJump(else_label, cond, "equal", NumberValue(0)) + \
                   code + MppInstructionJump(end_label) + MppInstructionLabel(else_label) + \
                   else_code + MppInstructionLabel(end_label)

        end_label = Gen.temp_lab()

        return cond_code + MppInstructionOJump(end_label, cond, "equal", NumberValue(0)) + code + \
               MppInstructionLabel(end_label)


class LoopNode(Node):
    """
    Loop.
    """

    def __init__(self, pos: Position):
        super().__init__(pos)


class WhileNode(LoopNode):
    """
    While loop.
    """

    name: str
    cond: Node
    code: CodeBlockNode

    def __init__(self, pos: Position, name: str, cond: Node, code: CodeBlockNode):
        super().__init__(pos)

        self.name = name
        self.cond = cond
        self.code = code

    def generate(self) -> Instruction | Instructions:
        self.code.push_scope()

        cond_code, cond = self.cond.get()

        code = self.code.generate()

        self.code.pop_scope()

        # check if the conditions is a number
        if cond.type != Type.NUM:
            Error.incompatible_types(self, cond.type, Type.NUM)

        return MppInstructionLabel(f"{self.name}_s") + MppInstructionLabel(f"{self.name}_c") + cond_code + \
               MppInstructionOJump(f"{self.name}_e", cond, "equal", NumberValue(0)) + \
               code + MppInstructionJump(f"{self.name}_s") + MppInstructionLabel(f"{self.name}_e")


class ForNode(LoopNode):
    """
    For loop.
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

    def generate(self) -> Instruction | Instructions:
        self.code.push_scope()

        init = self.init.generate()
        cond_code, cond = self.cond.get()
        action = self.action.generate()

        code = self.code.generate()

        self.code.pop_scope()

        # check if the condition is a number
        if cond.type != Type.NUM:
            Error.incompatible_types(self, cond.type, Type.NUM)

        return init + MppInstructionLabel(f"{self.name}_s") + cond_code + \
               MppInstructionOJump(f"{self.name}_e", cond, "equal", NumberValue(0)) + \
               code + MppInstructionLabel(f"{self.name}_c") + action + MppInstructionJump(f"{self.name}_s") + \
               MppInstructionLabel(f"{self.name}_e")


class RangeNode(LoopNode):
    """
    Range loop.
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

    def generate(self) -> Instruction | Instructions:
        self.var = Scopes.rename(self.var, True)

        # check if the counter variable is already defined
        if (var := Scopes.get(self.var)) is None:
            var = VariableValue(Type.NUM, self.var)
            Scopes.add(var)

        # check if the counter variable is already defined as a function
        elif isinstance(var, Function):
            Error.already_defined_var(self, self.var)

        # check if the counter variable is a number
        elif var.type != Type.NUM:
            Error.incompatible_types(self, var.type, Type.NUM)

        until_code, until = self.until.get()

        # check if the until condition is a number
        if until.type != Type.NUM:
            Error.incompatible_types(self, until.type, Type.NUM)

        code = MInstruction(MInstructionType.SET, [var, NumberValue(0)]) + MppInstructionLabel(f"{self.name}_s") + \
               until_code + MppInstructionOJump(f"{self.name}_e", var, "greaterThanEq", until) + \
               self.code.generate() + MppInstructionLabel(f"{self.name}_c") + \
               MInstruction(MInstructionType.OP, ["add", var, var, NumberValue(1)]) + \
               MppInstructionJump(f"{self.name}_s") + MppInstructionLabel(f"{self.name}_e")

        return code


class FunctionNode(Node):
    """
    Function definition.
    """

    name: str
    params: list[tuple[str, Type]]
    return_type: Type
    code: CodeBlockNode

    def __init__(self, pos: Position, name: str, params: list[tuple[str, Type]], return_type: Type, code: CodeBlockNode):
        super().__init__(pos)

        self.name = name
        self.params = params
        self.return_type = return_type
        self.code = code

    def __str__(self):
        return f"function {self.name} ({', '.join(map(lambda t: t[1].name + ' ' + t[0], self.params))}) {self.code}"

    def generate(self) -> Instruction | Instructions:
        # declare the function
        Scopes.add(Function(self.name, self.params, self.return_type))

        code = Instructions()

        code += MppInstructionJump(f"__f_{self.name}_end")
        code += MppInstructionLabel(f"__f_{self.name}")

        Scopes.push(self.name)
        # declare all parameters
        for name, type_ in self.params:
            Scopes.add(VariableValue(type_, Scopes.rename(name, True)))

        self.code.push_scope()

        code += self.code.generate()

        self.code.pop_scope()

        Scopes.pop()

        code += MInstruction(MInstructionType.SET, [
            VariableValue(Type.NUM, "@counter"),
            VariableValue(Type.NUM, f"__f_{self.name}_ret")
        ])
        code += MppInstructionLabel(f"__f_{self.name}_end")

        return code
