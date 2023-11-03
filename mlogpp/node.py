from __future__ import annotations

from typing import Callable

from .util import Position
from .values import *
from .generator import Gen
from .instruction import *
from .scope import Scope
from .abi import ABI
from .operations import Operations
from .enums import ENUM_TYPES_VALUES


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
        
        return Value.null()

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
    scope: bool

    def __init__(self, pos: Position, code: list[Node], scope: bool = False):
        super().__init__(pos)

        self.code = code
        self.scope = scope

    def __str__(self):
        if len(self.code) > 0:
            return "{\n" + "\n".join(map(str, self.code)) + "\n}"

        return "{}"

    def gen(self) -> Value:
        Node.gen(self)

        if self.scope:
            self.scope_push(Gen.tmp())
        
        for node in self.code[:-1]:
            node.gen()

        if len(self.code) > 0:
            return self.code[-1].gen()

        if self.scope:
            self.scope_pop()

        return Value.null()


class AsmBlockNode(Node):
    node: Node
    inputs: list[str]
    outputs: list[str]

    def __init__(self, pos: Position, node: Node, inputs: list[str], outputs: list[str]):
        super().__init__(pos)

        self.node = node
        self.inputs = inputs
        self.outputs = outputs

    def __str__(self):
        return f"asm ({', '.join(self.inputs)}) -> ({', '.join(self.outputs)}) {self.node}"

    def gen(self) -> Value:
        Node.gen(self)

        Gen.emit(*[
            InstructionSet(inp, self.scope_get(inp).get()) for inp in self.inputs
        ])
        self.node.gen()
        for output in self.outputs:
            out = self.scope_get(output)
            if out.const():
                Error.write_to_const(self, out.value)
            Gen.emit(
                InstructionSet(out.get(), output)
            )

        return Value.null()


class DeclarationNode(Node):
    type: str
    name: str
    value: Node | None
    is_block_special: bool
    const: bool
    const_on_write: bool

    def __init__(self, pos: Position, type_: str, name: str, value: Node | None,
                 is_block_special: bool = True, *, const: bool = False, const_on_write: bool = False):

        assert (not const) or (value is not None)

        super().__init__(pos)

        self.type = type_
        self.name = name
        self.value = value
        self.is_block_special = is_block_special
        self.const = const
        self.const_on_write = const_on_write

    def __str__(self):
        return f"{'const ' if self.const else ''}{'const_on_write ' if self.const_on_write else ''}{self.type} {self.name} = {self.value}"

    def gen(self) -> Value:
        Node.gen(self)

        if self.value is None:
            if self.type == "let":
                Error.custom(self.get_pos(), "Cannot infer type")

            type_ = self.parse_type(self.type)

            if self.type == "Block" and self.is_block_special:
                value = Value.variable(self.name, Type.BLOCK, True)
                self.scope_declare(self.name, value)

                return value

            else:
                value = Value.null()

        else:
            value = self.value.gen()

            if self.type == "let":
                type_ = value.type()

                if type_.is_private():
                    Error.private_type(self, type_)
            else:
                type_ = self.parse_type(self.type)

        if value.is_null():
            self.check_types(value.type(), type_)

        val = Value.variable(self.name, type_, self.const, const_on_write=self.const_on_write)
        val.value = self.scope_declare(self.name, val)

        if not value.is_null():
            val.set(value)

        return val


class MultiDeclarationNode(Node):
    type: str
    names: list[str]
    const_on_write: bool

    def __init__(self, pos: Position, type_: str, names: list[str], *, const_on_write: bool = False):
        super().__init__(pos)

        self.type = type_
        self.names = names
        self.const_on_write = const_on_write

    def __str__(self):
        return f"{self.type} {', '.join(self.names)}"

    def gen(self) -> Value:
        Node.gen(self)

        if self.type == "let":
            Error.custom(self.get_pos(), "Cannot infer type")

        type_ = self.parse_type(self.type)

        for name in self.names:
            val = Value.variable(name, type_, const_on_write=self.const_on_write)
            if self.type == "Block":
                self.scope_declare(name, val)
            else:
                val.value = self.scope_declare(name, val)

        return Value.null()


class ConfigNode(Node):
    type: str
    name: str
    value: Node

    def __init__(self, pos: Position, type_: str, name: str, value: Node):
        super().__init__(pos)

        self.type = type_
        self.name = name
        self.value = value

    def __str__(self):
        return f"configuration {self.type} {self.name} = {self.value}"

    def gen(self) -> Value:
        Node.gen(self)

        val = self.value.gen()

        if self.type == "let":
            type_ = val.type()

            if type_.is_private():
                Error.private_type(self, type_)
        else:
            type_ = self.parse_type(self.type)

        if val.type() not in type_:
            Error.incompatible_types(self, val.type(), type_)
        Scope.configurations[self.name] = val

        val = Value.variable(self.name, type_)
        Scope.scopes[2][self.name] = val

        return Value.null()


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
            Error.undefined_attribute(self, self.attr, value.value)

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

        return Value(Type.OBJECT, cell.get(), False, type_impl=IndexedTypeImpl(index))


class CallNode(Node):
    value: Node
    params: list[Node]

    END_LABEL: str = ""

    def __init__(self, pos: Position, value: Node, params: list[Node]):
        super().__init__(pos)

        self.value = value
        self.params = params

    def __str__(self):
        return f"{self.value}({','.join(map(str, self.params))})"

    def gen(self) -> Value:
        Node.gen(self)
        
        func = self.value.gen()

        if func.callable():
            if len(self.params) != len(func.get_params()):
                Error.invalid_arg_count(self, len(self.params), len(func.get_params()))

            params = []
            for param, type_ in zip(self.params, func.impl().get_params(func)):
                enum = {}
                for t in type_.list_types():
                    e = ENUM_TYPES_VALUES.get(t)
                    if e is not None:
                        enum |= e
                Scope.enum(enum)

                params.append(param.gen())

                Scope.enum()

            if func.impl().will_inline():
                impl = func.impl()
                assert isinstance(impl, BaseFunctionTypeImpl)

                if func.value in Scope.functions:
                    Error.custom(self.get_pos(), "Recursion is forbidden")

                self.scope_push(func.value)
                end_label = CallNode.END_LABEL
                CallNode.END_LABEL = Gen.tmp()
                for key, value in impl.scope.items():
                    Scope.scopes[-1][key] = value
                result = func.call(self, params)
                Gen.emit(
                    Label(CallNode.END_LABEL)
                )
                ret = Value.variable(Gen.tmp(), impl.ret)
                ret.set(result)
                result = ret
                for dst, src in impl.get_copies_after_call(func):
                    dst.set(src)
                CallNode.END_LABEL = end_label
                self.scope_pop()
                return result

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
            val = self.value.gen()
            Value.variable(ABI.function_return(func), val.type()).set(val)

        else:
            Value.variable(ABI.function_return(func), Type.NULL).set(Value.null())

        Gen.emit(
            InstructionJump(CallNode.END_LABEL, "always", 0, 0)
        )

        return Value.null()


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

        return Value.null()


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

        return Value.null()


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
        
        # self.scope_push(Gen.tmp())

        condition = self.condition.gen().get()
        lab1, lab2 = Gen.tmp(), None

        self.scope_push(Gen.tmp())

        Gen.emit(
            InstructionJump(lab1, "equal", condition, 0)
        )
        self.code.gen()
        if self.else_code is not None:
            lab2 = Gen.tmp()
            Gen.emit(
                InstructionJump(lab2, "always", 0, 0)
            )
        Gen.emit(
            Label(lab1)
        )

        if self.else_code is not None:
            self.else_code.gen()
            Gen.emit(
                Label(lab2)
            )

        self.scope_pop()

        return Value.null()


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
    a: Node
    b: Node | None
    code: Node

    def __init__(self, pos: Position, name: str, a: Node, b: Node | None, code: Node):
        super().__init__(pos)

        self.name = name
        self.a = a
        self.b = b
        self.code = code

    def __str__(self):
        return f"for ({self.name} : {self.a}{'..' if self.b is not None else ''}{self.b if self.b is not None else ''}) {self.code}"

    def gen(self) -> Value:
        Node.gen(self)
        
        name = ABI.loop_name(Gen.tmp())

        start = Gen.tmp()
        break_ = ABI.loop_break(name)
        continue_ = ABI.loop_continue(name)

        self.scope_push(name)

        counter = Value.variable(self.name, Type.NUM)
        counter.value = self.scope_declare(self.name, counter)

        Gen.emit(
            InstructionSet(counter, 0 if self.b is None else self.a.gen().get()),
            Label(start)
        )
        until = self.a.gen() if self.b is None else self.b.gen()
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
    params: list[tuple[str, str, bool]]
    return_type: str
    code: Node

    def __init__(self, pos: Position, name: str, params: list[tuple[str, str, bool]], return_type: str, code: Node):
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

        self.scope_push(name)

        params = []
        for type_, n, const in self.params:
            type_ = self.parse_type(type_)
            value = Value.variable(n, type_, const)
            value.value = self.scope_declare(n, value)
            params.append((type_, value.value))

        func_scope = Scope.scopes[-1]

        self.scope_pop()

        return_type = self.parse_type(self.return_type)

        function = Value(Type.function([param[0] for param in params], return_type), name, type_impl=FunctionTypeImpl(
            params, return_type, self.code, func_scope))

        self.scope_declare(self.name, function)

        return function


class MemberFunctionNode(Node):
    struct: str
    name: str
    params: list[tuple[str, str, bool]]
    return_type: str
    code: Node

    def __init__(self, pos: Position, struct: str, name: str, params: list[tuple[str, str, bool]], return_type: str, code: Node):
        super().__init__(pos)

        self.struct = struct
        self.name = name
        self.params = params
        self.return_type = return_type
        self.code = code

    def __str__(self):
        return f"function [member] {self.name}({', '.join(map(str, self.params))}) {self.code}"

    def gen(self) -> Value:
        Node.gen(self)

        name = ABI.struct_method(self.struct, self.name)

        self.scope_push(name)

        params = []
        for type_, n, const in self.params:
            type_ = self.parse_type(type_)
            value = Value.variable(n, type_, const)
            value.value = self.scope_declare(n, value)
            params.append((type_, value.value))

        func_scope = Scope.scopes[-1]

        self.scope_pop()

        return_type = self.parse_type(self.return_type)

        function = Value(Type.function([param[0] for param in params], return_type), name, type_impl=MemberFunctionTypeImpl(
            params, return_type, self.code, func_scope))

        return function


class CustomNode(Node):
    instructions: list[Instruction | Callable[[Node], Instruction]]

    def __init__(self, pos: Position, instructions: list[Instruction | Callable[[Node], Instruction]]):
        super().__init__(pos)

        self.instructions = instructions

    def gen(self) -> Value:
        for ins in self.instructions:
            if isinstance(ins, Instruction | BaseInstruction):
                Gen.emit(ins)
            else:
                i = ins(self)
                if i is not None:
                    Gen.emit(i)

        return Value.null()


class StructNode(Node):
    name: str
    fields: list[tuple[str, str]]
    functions: list[MemberFunctionNode]
    parents: list[str]

    def __init__(self, pos: Position, name: str, fields: list[tuple[str, str]],
                 functions: list[MemberFunctionNode], parents: list[str]):
        super().__init__(pos)

        self.name = name
        self.fields = fields
        self.functions = functions
        self.parents = parents

    def __str__(self):
        fields = "".join(f"{k} {v}\n" for k, v in self.fields)
        return f"struct {self.name} {{{fields}}}"

    def gen(self) -> Value:
        Node.gen(self)

        if self.name in Type.typenames:
            Error.already_defined_type(self, self.name)

        fields = self.fields.copy()
        parents = set()

        parent_methods = {}
        for name in self.parents:
            if name in parents:
                Error.custom(self.get_pos(), f"Duplicate struct parent [{name}]")
            parents.add(name)

            parent = self.parse_type(name)
            impl = TypeImpl.get_impl(parent)
            if isinstance(impl, StructTypeImpl):
                fields = impl.fields_with_typenames + fields

            else:
                Error.custom(self.get_pos(), f"Cannot inherit from [{name}]")

            for k, v in impl.methods.items():
                if k in parent_methods:
                    Error.already_defined_var(self, k)
                parent_methods[k] = v

        seen = set()
        for _, name in fields:
            if name in seen:
                Error.already_defined_var(self, name)
            seen.add(name)
        pos = self.get_pos()

        type_ = Type.simple(self.name)
        type_.convertible_to.update(parents)
        Type.register(self.name, type_)
        types = {v: self.parse_type(k) for k, v in fields}
        TypeImpl.add_impl(type_, StructTypeImpl(types, parent_methods, fields))
        impl = TypeImpl.get_impl(type_)
        assert isinstance(impl, StructTypeImpl)
        for func in self.functions:
            if func.name in seen:
                Error.already_defined_var(self, func.name)
            seen.add(func.name)

            impl.methods[func.name] = func.gen()
        struct = Value.variable(Gen.tmp(), type_)
        if type_ in types.values():
            Error.custom(self.get_pos(), f"Recursive struct not allowed")
        constructor = FunctionNode(pos, self.name, [f + (False,) for f in fields], self.name, BlockNode(self.get_pos(), [
            CustomNode(pos, [
                lambda s: Value.variable(struct.value, type_).set(Value(type_, "null", type_impl=StructSourceTypeImpl({
                    field: s.scope_get(field) for field in types.keys()
                })))
            ]),
            ReturnNode(pos, StructValueNode(self.get_pos(), struct.value, type_)),
            CustomNode(pos, [])
        ]))
        constructor.gen()

        return Value.null()


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

        if isinstance(self.value, float) and self.value.is_integer():
            self.value = int(self.value)

    def gen(self) -> Value:
        Node.gen(self)
        
        return Value.number(self.value)


class StringValueNode(ValueNode):
    value: str

    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

    def gen(self) -> Value:
        Node.gen(self)
        
        return Value.string(self.value)


class StructValueNode(ValueNode):
    value: str
    type: Type

    def __init__(self, pos: Position, value: str, type_: Type):
        super().__init__(pos, value)

        self.type = type_

    def gen(self) -> Value:
        Node.gen(self)

        return Value(self.type, self.value)


class ColorValueNode(ValueNode):
    value: str


    def __init__(self, pos: Position, value: str):
        super().__init__(pos, value)

        self.value = value

    def gen(self) -> Value:
        Node.gen(self)

        return Value(Type.COLOR, self.value)
