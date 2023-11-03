from __future__ import annotations

from .value_types import Type
from .generator import Gen
from .instruction import InstructionSet, InstructionRead, InstructionWrite, InstructionControl, InstructionSensor, InstructionOp
from .abi import ABI
from .error import Error
from .content import Content


class Value:
    _type: Type
    value: str
    _const: bool
    _type_impl: TypeImpl
    _const_on_write: bool

    def __init__(self, type_: Type, value: str, const: bool = True, *,
                 type_impl: TypeImpl = None, const_on_write: bool = False):
        self._type = type_
        self.value = value
        self._const = const
        self._type_impl = TypeImpl.get_impl(self._type) if type_impl is None else type_impl
        self._const_on_write = const_on_write

    def __eq__(self, other):
        if isinstance(other, Value):
            return self.type() == other.type() and self.value == other.value and self._type_impl == other._type_impl

    @classmethod
    def null(cls) -> Value:
        return Value(Type.NULL, "null")

    @classmethod
    def number(cls, val: int | float | str) -> Value:
        return Value(Type.NUM, str(val))

    @classmethod
    def string(cls, val: str) -> Value:
        return Value(Type.STR, val)

    @classmethod
    def variable(cls, name: str, type_: Type, const: bool = False, *, const_on_write: bool = False) -> Value:
        return Value(type_, name, const, const_on_write=const_on_write)

    def is_null(self) -> bool:
        return self.type() in Type.NULL

    def impl(self) -> TypeImpl:
        return self._type_impl

    def type(self) -> Type:
        return self._type

    def type_get(self) -> Type:
        return self._type_impl.type_get(self)

    def type_set(self) -> Type:
        return self._type_impl.type_set(self)

    def const(self) -> bool:
        return self._const

    def callable(self) -> bool:
        return self._type_impl.callable(self)

    def get(self) -> str:
        return self._type_impl.get(self)

    def get_as(self, type_: Type) -> Value | None:
        return self._type_impl.get_as(self, type_)

    def set(self, value: Value):
        if self.const():
            raise TypeError("Assignment to const variable")

        self._type_impl.set(self, value)
        if self._const_on_write:
            self._const = True

    def write(self, cell: Value, index: Value):
        self._type_impl.write(self, cell, index)

    def read(self, cell: Value, index: Value):
        if self.const():
            raise TypeError("Assignment to const variable")

        self._type_impl.read(self, cell, index)

    def getattr(self, name: str) -> Value | None:
        return self._type_impl.getattr(self, name)

    def call(self, node, params: list[Value]) -> Value:
        if not self.callable():
            raise TypeError("Trying to call non callable value")

        return self._type_impl.call(self, node, params)

    def get_params(self) -> list[Type]:
        if not self.callable():
            raise TypeError("Trying to call non callable value")

        return self._type_impl.get_params(self)

    def outputs(self) -> list[int]:
        if not self.callable():
            raise TypeError("Trying to call non callable value")

        return self._type_impl.outputs(self)


class TypeImpl:
    _IMPLEMENTATIONS: dict[Type, TypeImpl] = {}
    _DEFAULT_IMPL: TypeImpl = None

    @classmethod
    def add_impl(cls, type_: Type, impl: TypeImpl):
        cls._IMPLEMENTATIONS[type_] = impl

    @classmethod
    def get_impl(cls, type_: Type) -> TypeImpl:
        return cls._IMPLEMENTATIONS.get(type_, cls._DEFAULT_IMPL)

    def get(self, value: Value) -> str:
        return value.value

    def get_as(self, value: Value, type_: Type) -> Value | None:
        return None

    def set(self, value: Value, source: Value):
        Gen.emit(
            InstructionSet(value.value, source.get())
        )

    def type_get(self, value: Value) -> Type:
        return value.type()

    def type_set(self, value: Value) -> Type:
        return value.type()

    def write(self, value: Value, cell: Value, index: Value) -> int:
        Gen.emit(
            InstructionWrite(value.get(), cell.value, index.get())
        )
        return 1

    def read(self, value: Value, cell: Value, index: Value) -> int:
        val = Gen.tmp()
        Gen.emit(
            InstructionRead(val, cell.value, index.get())
        )
        value.set(Value(value.type(), val, False))
        return 1

    def getattr(self, value: Value, name: str) -> Value | None:
        if name in Content.CONTROLLABLE and value.type() in Type.BLOCK:
            return Value(Content.CONTROLLABLE[name], value.get(), False, type_impl=ControlSensorTypeImpl(name))

        elif name in Content.SENSABLE and value.type() in Type.BLOCK | Type.UNIT:
            return Value(Content.SENSABLE[name], value.get(), True, type_impl=ControlSensorTypeImpl(name))

        return None

    def callable(self, value: Value) -> bool:
        return False

    def call(self, value: Value, node, params: list[Value]) -> Value:
        raise NotImplementedError

    def get_params(self, value: Value) -> list[Type]:
        raise NotImplementedError

    def outputs(self, value: Value) -> list[int]:
        return []

    def will_inline(self) -> bool:
        return False

    def get_copies_after_call(self, value: Value) -> list[tuple[Value, Value]]:
        return []


TypeImpl._DEFAULT_IMPL = TypeImpl()


class IndexedTypeImpl(TypeImpl):
    index: Value

    def __init__(self, index: Value):
        self.index = index

    def get(self, value: Value) -> str:
        val = Value.variable(Gen.tmp(), Type.NUM)
        val.read(value, self.index)
        return val.get()

    def get_as(self, value: Value, type_: Type) -> Value | None:
        val = Value.variable(Gen.tmp(), type_)
        val.read(value, self.index)
        return val

    def set(self, value: Value, source: Value):
        source.write(value, self.index)

    def type_get(self, value: Value) -> Type:
        return Type.NUM

    def type_set(self, value: Value) -> Type:
        return Type.ANY


class StructSourceTypeImpl(TypeImpl):
    fields: dict[str, Value]

    def __init__(self, fields: dict[str, Value]):
        self.fields = fields

    def get(self, value: Value) -> str:
        return "null"

    def getattr(self, value: Value, name: str) -> Value | None:
        return self.fields.get(name)


class StructTypeImpl(TypeImpl):
    fields: dict[str, Type]
    methods: dict[str, Value]
    fields_with_typenames: list[tuple[str, str]]

    def __init__(self, fields: dict[str, Type], methods: dict[str, Value], fields_with_typenames: list[tuple[str, str]]):
        self.fields = fields
        self.methods = methods
        self.fields_with_typenames = fields_with_typenames

    def get(self, value: Value) -> str:
        return "null"

    def set(self, value: Value, source: Value):
        if source.is_null():
            for field in self.fields.keys():
                value.getattr(field).set(Value.null())

            return

        impl = source.impl()
        if isinstance(impl, StructTypeImpl):
            for field in self.fields.keys() & impl.fields.keys():
                value.getattr(field).set(source.getattr(field))
        elif isinstance(impl, IndexedTypeImpl):
            value.read(source, impl.index)
        else:
            for field in self.fields.keys():
                value.getattr(field).set(source.getattr(field))

    def write(self, value: Value, cell: Value, index: Value) -> int:
        i = 0
        for name in self.fields.keys():
            val = self.getattr(value, name)
            offset = index
            if i != 0:
                offset = Value.variable(Gen.tmp(), Type.NUM)
                Gen.emit(
                    InstructionOp("add", offset.value, index.get(), i)
                )
            i += val.impl().write(val, cell, offset)
        return i

    def read(self, value: Value, cell: Value, index: Value) -> int:
        i = 0
        for name in self.fields.keys():
            val = self.getattr(value, name)
            offset = index
            if i != 0:
                offset = Value.variable(Gen.tmp(), Type.NUM)
                Gen.emit(
                    InstructionOp("add", offset.value, index.get(), i)
                )
            i += val.impl().read(val, cell, offset)
        return i

    def getattr(self, value: Value, name: str) -> Value | None:
        if name in self.fields:
            return Value(self.fields[name], ABI.struct_field(value.value, name), value.const())

        elif name in self.methods:
            method = self.methods[name]
            impl = method.impl()
            assert isinstance(impl, BaseFunctionTypeImpl)

            if value.const() and not impl.scope["self"].const():
                Error.custom(node_module.Node.current.get_pos(), f"Calling method with non-const [self] on const struct")

            return Value(method.type(), method.value, type_impl=ClosureTypeImpl(impl.scope, method, [(0, value)]))

        return None


class BaseFunctionTypeImpl(TypeImpl):
    params: list[tuple[Type, str]]
    ret: Type
    scope: dict[str, Value]

    def __init__(self, params: list[tuple[Type, str]], ret: Type, scope: dict[str, Value]):
        self.params = params
        self.ret = ret
        self.scope = scope


class ClosureTypeImpl(BaseFunctionTypeImpl):
    func: Value
    insertions: list[tuple[int, Value]]

    def __init__(self, scope, func: Value, insertions: list[tuple[int, Value]]):
        impl = func.impl()
        assert isinstance(impl, BaseFunctionTypeImpl)
        super().__init__(impl.params, impl.ret, impl.scope)

        self.scope = scope
        self.func = func
        self.insertions = insertions

    def callable(self, value: Value) -> bool:
        return self.func.impl().callable(value)

    def call(self, value: Value, node, params: list[Value]) -> Value:
        par = params.copy()
        for i, v, in self.insertions:
            if i == -1:
                par.append(v)
            else:
                par.insert(i, v)
        return self.func.impl().call(value, node, par)

    def get_params(self, value: Value) -> list[Type]:
        return self.func.impl().get_params(value)

    def will_inline(self) -> bool:
        return self.func.impl().will_inline()

    def get_copies_after_call(self, value: Value) -> list[tuple[Value, Value]]:
        return self.func.impl().get_copies_after_call(value)


class MemberFunctionTypeImpl(BaseFunctionTypeImpl):
    def __init__(self, params: list[tuple[Type, str]], ret: Type, code, scope: dict[str, Value]):
        super().__init__(params, ret, scope)
        self.code = code

    def callable(self, value: Value) -> bool:
        return True

    def call(self, value: Value, node, params: list[Value]) -> Value:
        if len(self.params) != len(params):
            Error.invalid_arg_count(node, len(params), len(self.params))

        value.last_params = params

        for i, [type_, name] in enumerate(self.params):
            if params[i].type() not in type_:
                Error.incompatible_types(node, params[i].type(), type_)

            Value.variable(name, type_).set(params[i])

        self.code.gen()

        Value.variable(ABI.function_return(value.value), self.ret).set(Value.null())

        return Value.variable(ABI.function_return(value.value), self.ret)

    def get_params(self, value: Value) -> list[Type]:
        return [param[0] for param in self.params[1:]]

    def will_inline(self) -> bool:
        return True

    def get_copies_after_call(self, value: Value) -> list[tuple[Value, Value]]:
        if self.scope["self"].const():
            return []
        return [(value.last_params[0], Value.variable(self.params[0][1], self.params[0][0]))]


class FunctionTypeImpl(BaseFunctionTypeImpl):
    params: list[tuple[Type, str]]
    ret: Type
    scope: dict[str, Value]

    def __init__(self, params: list[tuple[Type, str]], ret: Type, code, scope: dict[str, Value]):
        super().__init__(params, ret, scope)
        self.code = code

    def callable(self, value: Value) -> bool:
        return True

    def call(self, value: Value, node, params: list[Value]) -> Value:
        if len(self.params) != len(params):
            Error.invalid_arg_count(node, len(params), len(self.params))

        for i, [type_, name] in enumerate(self.params):
            if params[i].type() not in type_:
                Error.incompatible_types(node, params[i].type(), type_)

            Value.variable(name, type_).set(params[i])

        self.code.gen()

        Value.variable(ABI.function_return(value.value), self.ret).set(Value.null())

        return Value.variable(ABI.function_return(value.value), self.ret)

    def get_params(self, value: Value) -> list[Type]:
        return [param[0] for param in self.params]

    def will_inline(self) -> bool:
        return True


class ControlSensorTypeImpl(TypeImpl):
    attrib: str

    def __init__(self, attrib: str):
        self.attrib = attrib

    def get(self, value: Value) -> str:
        if self.attrib in Content.SENSABLE:
            val = Gen.tmp()
            Gen.emit(
                InstructionSensor(val, value.value, "@" + self.attrib)
            )
            return val

        return "null"

    def set(self, value: Value, source: Value):
        Gen.emit(
            InstructionControl(self.attrib, value.value, source.get(), 0, 0, 0)
        )


from . import node as node_module
