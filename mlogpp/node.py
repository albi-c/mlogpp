from __future__ import annotations

from .util import Position
from .error import Error
from .values import *
from .generator import Gen
from .instruction import *
from .scope import Scope
from .abi import ABI
from .operations import Operations
from .enums import ENUM_TYPES


class Node:
    """
        Base node class.
        """

    pos: Position

    current: Node = None

    def __init__(self, pos: Position):
        self.pos = pos

        Error.node_class = Node

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
        Node.current = self
        
        return NullValue()

    def check_types(self, a: Type, b: Type):
        if a in b:
            return

        Error.incompatible_types(self, a, b)

    def parse_type(self, type_: str) -> Type:
        return Type.parse(type_, self)

    @staticmethod
    def scope_push(name: str):
        Scope.push(name)

    @staticmethod
    def scope_pop():
        Scope.pop()

    @staticmethod
    def scope_name() -> str:
        return Scope.name()

    @staticmethod
    def scope_function() -> str | None:
        return Scope.function()

    @staticmethod
    def scope_loop() -> str | None:
        return Scope.loop()

    def scope_get(self, name: str) -> Value:
        return Scope.get(self, name)

    def scope_set(self, name: str, value: Value):
        Scope.set(self, name, value)

    def scope_delete(self, name: str):
        Scope.delete(self, name)

    def scope_declare(self, name: str, value: Value) -> str:
        return Scope.declare(self, name, value)

    def do_operation(self, a: Value, op: str, b: Value | None = None) -> Value:
        if b is None:
            result = Operations.unary(op, a)

            if result is None:
                Error.invalid_operation(self, a.type(), op)

            elif isinstance(result, Value):
                return result

            else:
                result(self)

        else:
            result = Operations.binary(a, op, b)

            if result is None:
                Error.invalid_operation(self, a.type(), op, b.type())

            elif isinstance(result, Value):
                return result

            else:
                result(self)


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
        Node.gen(self)
        
        for node in self.code[:-1]:
            node.gen()

        if len(self.code) > 0:
            return self.code[-1].gen()

        return NullValue()


class DeclarationNode(Node):
    type: str
    name: str
    value: Node | None

    def __init__(self, pos: Position, type_: str, name: str, value: Node | None):
        super().__init__(pos)

        self.type = type_
        self.name = name
        self.value = value

    def __str__(self):
        return f"{self.type} {self.name} = {self.value}"

    def gen(self) -> Value:
        Node.gen(self)
        
        type_ = self.parse_type(self.type)

        if self.value is None:
            if self.type == "Block":
                value = VariableValue(self.name, Type.BLOCK, True)
                self.scope_declare(self.name, value)

                return NullValue()

            else:
                value = NullValue()

        else:
            value = self.value.gen()

        self.check_types(value.type(), type_)

        val = VariableValue(self.name, type_)
        val.name = self.scope_declare(self.name, val)

        if value != NullValue():
            val.set(value)

        return NullValue()


class MultiDeclarationNode(Node):
    type: str
    names: list[str]

    def __init__(self, pos: Position, type_: str, names: list[str]):
        super().__init__(pos)

        self.type = type_
        self.names = names

    def __str__(self):
        return f"{self.type} {', '.join(self.names)}"

    def gen(self) -> Value:
        type_ = self.parse_type(self.type)

        for name in self.names:
            val = VariableValue(name, type_)
            if self.type == "Block":
                self.scope_declare(name, val)
            else:
                val.name = self.scope_declare(name, val)

        return NullValue()


class UnaryOpNode(Node):
    op: str
    value: Node

    def __init__(self, pos: Position, op: str, value: Node):
        super().__init__(pos)

        self.op = op
        self.value = value

    def __str__(self):
        return f"{self.op}{self.value}"

    def gen(self) -> Value:
        Node.gen(self)
        
        return self.do_operation(self.value.gen(), self.op)


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
        Node.gen(self)
        
        return self.do_operation(self.left.gen(), self.op, self.right.gen())


class AttributeNode(Node):
    value: Node
    attr: str

    def __init__(self, pos: Position, value: Node, attr: str):
        super().__init__(pos)

        self.value = value
        self.attr = attr

    def __str__(self):
        return f"{self.value}.{self.attr}"

    def gen(self) -> Value:
        Node.gen(self)
        
        value = self.value.gen()

        attr = value.getattr(self.attr)

        if attr is None:
            Error.undefined_attribute(self, self.attr, value)

        else:
            return attr


class IndexNode(Node):
    cell: Node
    index: Node

    def __init__(self, pos: Position, cell: Node, index: Node):
        super().__init__(pos)

        self.cell = cell
        self.index = index

    def __str__(self):
        return f"{self.cell}[{self.index}]"

    def gen(self) -> Value:
        Node.gen(self)
        
        cell = self.cell.gen()
        index = self.index.gen()

        return IndexedValue(cell.get(), index.get())


class CallNode(Node):
    value: Node
    params: list[Node]

    def __init__(self, pos: Position, value: Node, params: list[Node]):
        super().__init__(pos)

        self.value = value
        self.params = params

    def __str__(self):
        return f"{self.value}({','.join(map(str, self.params))})"

    def gen(self) -> Value:
        Node.gen(self)
        
        func = self.value.gen()

        if isinstance(func, CallableValue):
            if len(self.params) != len(func.get_params()):
                Error.invalid_arg_count(self, len(self.params), len(func.get_params()))

            params = []
            for param, type_ in zip(self.params, func.get_params()):
                enum = {}
                for t in type_.list_types():
                    e = ENUM_TYPES.get(t)
                    if e is not None:
                        enum |= e.values
                Scope.enum(enum)

                params.append(param.gen())

                Scope.enum()

            return func.call(self, params)

        Error.not_callable(self, func)


class ReturnNode(Node):
    value: Node | None

    def __init__(self, pos: Position, value: Node | None):
        super().__init__(pos)

        self.value = value

    def __str__(self):
        return f"return {self.value if self.value is not None else ''}"

    def gen(self) -> Value:
        Node.gen(self)
        
        if (func := self.scope_function()) is None:
            Error.custom(self.get_pos(), "Return outside of a function")

        if self.value is not None:
            Gen.emit(
                InstructionSet(ABI.function_return(func), self.value.gen().get())
            )

        else:
            Gen.emit(
                InstructionSet(ABI.function_return(func), "null")
            )

        Gen.emit(
            InstructionSet("@counter", ABI.function_return_pos(func))
        )

        return NullValue()


class BreakNode(Node):
    def __init__(self, pos: Position):
        super().__init__(pos)

    def __str__(self):
        return "break"

    def gen(self) -> Value:
        Node.gen(self)
        
        if (loop := self.scope_loop()) is None:
            Error.custom(self.get_pos(), "Break outside of a loop")

        Gen.emit(
            InstructionJump(ABI.loop_break(loop), "always", 0, 0)
        )

        return NullValue()


class ContinueNode(Node):
    def __init__(self, pos: Position):
        super().__init__(pos)

    def __str__(self):
        return "continue"

    def gen(self) -> Value:
        Node.gen(self)
        
        if (loop := self.scope_loop()) is None:
            Error.custom(self.get_pos(), "Continue outside of a loop")

        Gen.emit(
            InstructionJump(ABI.loop_continue(loop), "always", 0, 0)
        )

        return NullValue()


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

    def gen(self) -> Value:
        Node.gen(self)
        
        self.scope_push(Gen.tmp())

        condition = self.condition.gen().get()
        lab1, lab2 = Gen.tmp(), None
        result = Gen.tmp()
        result2 = NullValue()

        Gen.emit(
            InstructionJump(lab1, "equal", condition, 0)
        )
        result1 = self.code.gen()
        Gen.emit(
            InstructionSet(result, result1.get())
        )
        if self.else_code is not None:
            lab2 = Gen.tmp()
            Gen.emit(
                InstructionJump(lab2, "always", 0, 0)
            )
        Gen.emit(
            Label(lab1)
        )

        if self.else_code is not None:
            result2 = self.else_code.gen()
            Gen.emit(
                InstructionSet(result, result2.get()),
                Label(lab2)
            )

        self.scope_pop()

        if self.else_code is not None and result1.type() == result2.type():
            return VariableValue(result, result1.type())

        return NullValue()


class WhileNode(Node):
    condition: Node
    code: Node

    def __init__(self, pos: Position, condition: Node, code: Node):
        super().__init__(pos)

        self.condition = condition
        self.code = code

    def __str__(self):
        return f"while ({self.condition}) {self.code}"

    def gen(self) -> Value:
        Node.gen(self)
        
        name = ABI.loop_name(Gen.tmp())

        break_ = ABI.loop_break(name)
        continue_ = ABI.loop_continue(name)

        self.scope_push(name)

        Gen.emit(
            Label(continue_)
        )
        condition = self.condition.gen()
        Gen.emit(
            InstructionJump(break_, "equal", condition, 0)
        )
        result = self.code.gen()
        Gen.emit(
            InstructionJump(continue_, "always", 0, 0),
            Label(break_)
        )

        self.scope_pop()

        return result


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

    def gen(self) -> Value:
        Node.gen(self)
        
        name = ABI.loop_name(Gen.tmp())

        start = Gen.tmp()
        break_ = ABI.loop_break(name)
        continue_ = ABI.loop_continue(name)

        self.scope_push(name)

        self.init.gen()
        Gen.emit(
            Label(start)
        )
        condition = self.condition.gen()
        Gen.emit(
            InstructionJump(break_, "equal", condition.get(), 0)
        )
        result = self.code.gen()
        Gen.emit(
            Label(continue_)
        )
        self.action.gen()
        Gen.emit(
            InstructionJump(start, "always", 0, 0),
            Label(break_)
        )

        self.scope_pop()

        return result


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
        Node.gen(self)
        
        name = ABI.loop_name(Gen.tmp())

        start = Gen.tmp()
        break_ = ABI.loop_break(name)
        continue_ = ABI.loop_continue(name)

        self.scope_push(name)

        counter = VariableValue(self.name, Type.NUM)
        counter.name = self.scope_declare(self.name, counter)

        Gen.emit(
            InstructionSet(counter, 0),
            Label(start)
        )
        until = self.until.gen()
        Gen.emit(
            InstructionJump(break_, "greaterThanEq", counter, until)
        )
        result = self.code.gen()
        Gen.emit(
            Label(continue_),
            InstructionOp("add", counter, counter, 1),
            InstructionJump(start, "always", 0, 0),
            Label(break_)
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

    def gen(self) -> Value:
        Node.gen(self)
        
        name = ABI.function_name(self.name)

        end = Gen.tmp()

        self.scope_push(name)

        params = []
        for type_, name in self.params:
            type_ = self.parse_type(type_)
            value = VariableValue(name, type_)
            value.name = self.scope_declare(name, value)
            params.append((type_, value.name))

        Gen.emit(
            InstructionJump(end, "always", 0, 0),
            Label(name)
        )
        self.code.gen()
        Gen.emit(
            InstructionSet(ABI.function_return(name), "null"),
            InstructionSet("@counter", ABI.function_return_pos(name)),
            Label(end)
        )

        self.scope_pop()

        return_type = self.parse_type(self.return_type)

        self.scope_declare(self.name, FunctionValue(name, params, return_type))

        return VariableValue(ABI.function_return(name), return_type)


class ValueNode(Node):
    def __init__(self, pos: Position, value):
        super().__init__(pos)

        self.value = value

    def __str__(self):
        return str(self.value)

    def gen(self) -> Value:
        raise NotImplementedError


class VariableValueNode(ValueNode):
    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def gen(self) -> Value:
        Node.gen(self)
        
        return self.scope_get(self.value)


class NumberValueNode(ValueNode):
    value: int | float

    def __init__(self, pos: Position, value: int | float):
        super().__init__(pos, value)

        if self.value.is_integer():
            self.value = int(self.value)

    def gen(self) -> Value:
        Node.gen(self)
        
        return NumberValue(self.value)


class StringValueNode(ValueNode):
    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def gen(self) -> Value:
        Node.gen(self)
        
        return StringValue(self.value)
