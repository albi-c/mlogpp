import typed_ast.ast3

from .util import Position
from .error import Error
from .values import *
from .generator import Gen
from .instruction import *
from .scope import Scope


class Node:
    """
        Base node class.
        """

    pos: Position

    def __init__(self, pos: Position):
        self.pos = pos

    def __str__(self):
        """
        Convert the node to a string, debug only.

        Returns:
            A string, similar to the unparsed mlog++ code.
        """

        return "NODE"

    def get_pos(self) -> Position:
        """
        Get position of the node.

        Returns:
            Position of the node.
        """

        return self.pos

    def gen(self) -> Value:
        return NullValue()

    def check_types(self, a: Type, b: Type):
        if a in b:
            return

        Error.incompatible_types(self, a, b)

    def parse_type(self, type_: str) -> Type:
        return Type.parse(type_, self)

    @staticmethod
    def scope_push():
        Scope.push()

    @staticmethod
    def scope_pop():
        Scope.pop()

    def scope_get(self, name: str) -> Value:
        return Scope.get(self, name)

    def scope_set(self, name: str, value: Value):
        Scope.set(self, name, value)

    def scope_delete(self, name: str):
        Scope.delete(self, name)

    def scope_declare(self, name: str, value: Value):
        Scope.declare(self, name, value)

    def do_operation(self, a: Value, op: str, b: Value | None = None) -> Value:
        if b is None:
            result = a.op_unary(op)
            if result is None:
                Error.invalid_operation(self, a, op)

            return result

        else:
            result = a.op_binary(op, b)
            if result is None:
                Error.invalid_operation(self, a, op, b)

            return result


class BlockNode(Node):
    code: list[Node]

    def __init__(self, pos: Position, code: list[Node]):
        super().__init__(pos)

        self.code = code

    def __str__(self):
        if len(self.code) > 0:
            return "{\n" + "\n".join(map(str, self.code)) + "\n}"

        return "{}"

    def gen(self) -> Value:
        for node in self.code[:-1]:
            node.gen()

        if len(self.code) > 0:
            return self.code[-1].gen()

        return NullValue()


class DeclarationNode(Node):
    type: str
    name: str
    value: Node

    def __init__(self, pos: Position, type_: str, name: str, value: Node):
        super().__init__(pos)

        self.type = type_
        self.name = name
        self.value = value

    def __str__(self):
        return f"{self.type} {self.name} = {self.value}"

    def gen(self) -> Value:
        type_ = self.parse_type(self.type)
        value = self.value.gen()

        self.check_types(value.type(), type_)

        Gen.emit(
            InstructionSet(self.name, value)
        )

        self.scope_declare(self.name, VariableValue(self.name, type_))

        return NullValue()


class BinaryOpNode(Node):
    left: Node
    op: str
    right: Node

    def __init__(self, pos: Position, left: Node, op: str, right: Node):
        super().__init__(pos)

        self.left = left
        self.op = op
        self.right = right

    def __str__(self):
        return f"{self.left} {self.op} {self.right}"

    def gen(self) -> Value:
        return self.do_operation(self.left.gen(), self.op, self.right.gen())


class UnaryOpNode(Node):
    op: str
    value: Node

    def __init__(self, pos: Position, op: str, value: Node):
        super().__init__(pos)

        self.left = left
        self.op = op
        self.value = value

    def __str__(self):
        return f"{self.op}{self.value}"

    def gen(self) -> Value:
        return self.do_operation(self.value.gen(), self.op)


class IndexNode(Node):
    value: Node
    index: Node

    def __init__(self, pos: Position, value: Node, index: Node):
        super().__init__(pos)

        self.value = value
        self.index = index

    def __str__(self):
        return f"{self.value}[{self.index}]"


class CallNode(Node):
    value: Node
    params: list[Node]

    def __init__(self, pos: Position, value: Node, params: list[Node]):
        super().__init__(pos)

        self.value = value
        self.params = params

    def __str__(self):
        return f"{self.value}({','.join(map(str, self.params))})"


class ReturnNode(Node):
    value: Node | None

    def __init__(self, pos: Position, value: Node | None):
        super().__init__(pos)

        self.value = value

    def __str__(self):
        return f"return {self.value if self.value is not None else ''}"


class BreakNode(Node):
    def __init__(self, pos: Position):
        super().__init__(pos)

    def __str__(self):
        return "break"


class ContinueNode(Node):
    def __init__(self, pos: Position):
        super().__init__(pos)

    def __str__(self):
        return "continue"


class EndNode(Node):
    def __init__(self, pos: Position):
        super().__init__(pos)

    def __str__(self):
        return "end"


class IfNode(Node):
    condition: Node
    code: Node
    else_code: Node | None

    def __init__(self, pos: Position, condition: Node, code: Node, else_code: Node | None):
        super().__init__(pos)

        self.condition = condition
        self.code = code
        self.else_code = else_code

    def __str__(self):
        return f"if ({self.condition}) {self.code}" + (f"else {self.else_code}" if self.else_code is not None else "")


class WhileNode(Node):
    condition: Node
    code: Node

    def __init__(self, pos: Position, condition: Node, code: Node):
        super().__init__(pos)

        self.condition = condition
        self.code = code

    def __str__(self):
        return f"while ({self.condition}) {self.code}"


class ForNode(Node):
    init: Node
    condition: Node
    action: Node
    code: Node

    def __init__(self, pos: Position, init: Node, condition: Node, action: Node, code: Node):
        super().__init__(pos)

        self.init = init
        self.condition = condition
        self.action = action
        self.code = code

    def __str__(self):
        return f"for ({self.init}; {self.condition}; {self.action}) {self.code}"


class RangeNode(Node):
    name: str
    until: Node
    code: Node

    def __init__(self, pos: Position, name: str, until: Node, code: Node):
        super().__init__(pos)

        self.name = name
        self.until = until
        self.code = code

    def __str__(self):
        return f"for ({self.name} : {self.until}) {self.code}"

    def gen(self) -> Value:
        self.scope_push()

        counter = VariableValue(self.name, Type.NUM)
        self.scope_declare(self.name, counter)

        start = Gen.tmp()
        end = Gen.tmp()

        Gen.emit(
            InstructionSet(counter, 0),
            Label(start)
        )
        until = self.until.gen()
        Gen.emit(
            InstructionJump(end, "greaterThanEq", counter, until)
        )
        result = self.code.gen()
        Gen.emit(
            InstructionJump(start),
            Label(end)
        )

        self.scope_pop()

        return result


class FunctionNode(Node):
    name: str
    params: list[tuple[str, str]]
    return_type: str
    code: Node

    def __init__(self, pos: Position, name: str, params: list[tuple[str, str]], return_type: str, code: Node):
        super().__init__(pos)

        self.name = name
        self.params = params
        self.return_type = return_type
        self.code = code

    def __str__(self):
        return f"function {self.name}({', '.join(map(str, self.params))}) {self.code}"


class ValueNode(Node):
    def __init__(self, pos: Position, value):
        super().__init__(pos)

        self.value = value

    def __str__(self):
        return str(self.value)


class VariableValueNode(ValueNode):
    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def gen(self) -> Value:
        return self.scope_get(self.value)


class NumberValueNode(ValueNode):
    value: int | float

    def __init__(self, pos: Position, value: int | float):
        super().__init__(pos, value)

        if self.value.is_integer():
            self.value = int(self.value)

    def gen(self) -> Value:
        return NumberValue(self.value)


class StringValueNode(ValueNode):
    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def gen(self) -> Value:
        return StringValue(self.value)
