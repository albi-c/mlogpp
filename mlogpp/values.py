from __future__ import annotations

from .value_types import Type
from .generator import Gen
from .instruction import InstructionSet, InstructionRead, InstructionWrite, InstructionControl, InstructionSensor
from .abi import ABI
from .error import Error
from .content import Content


class Value:
    _type: Type
    value: str
    _const: bool
    _type_impl: TypeImpl

    def __init__(self, type_: Type, value: str, const: bool = True, *, type_impl: TypeImpl = None):
        self._type = type_
        self.value = value
        self._const = const
        self._type_impl = TypeImpl.get_impl(self._type) if type_impl is None else type_impl

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
    def function(cls, name: str, params: list[tuple[Type, str]], ret: Type, code) -> Value:
        return Value(Type.function([p[0] for p in params], ret), name, type_impl=FunctionTypeImpl(params, ret, code))

    @classmethod
    def variable(cls, name: str, type_: Type, const: bool = False) -> Value:
        return Value(type_, name, const)

    def is_null(self) -> bool:
        return self.get() == "null" or self.type() in Type.NULL

    def impl(self) -> TypeImpl:
        return self._type_impl

    def type(self) -> Type:
        return self._type

    def const(self) -> bool:
        return self._const

    def callable(self) -> bool:
        return self._type_impl.callable(self)

    def get(self) -> str:
        return self._type_impl.get(self)

    def set(self, value: Value):
        if self.const():
            raise TypeError("Assignment to const variable")

        return self._type_impl.set(self, value)

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

    def set(self, value: Value, source: Value):
        Gen.emit(
            InstructionSet(value.value, source.get())
        )

    def write(self, value: Value, cell: Value, index: Value):
        Gen.emit(
            InstructionWrite(value.get(), cell.value, index.get())
        )

    def read(self, value: Value, cell: Value, index: Value):
        val = Gen.tmp()
        Gen.emit(
            InstructionRead(val, cell.value, index.get())
        )
        value.set(Value(value.type(), val, False))

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


class IndexedTypeImpl(TypeImpl):
    index: Value

    def __init__(self, index: Value):
        self.index = index

    def get(self, value: Value) -> str:
        val = Value.variable(Gen.tmp(), Type.NUM)
        val.read(value, self.index)
        return val.get()

    def set(self, value: Value, source: Value):
        source.write(value, self.index)


TypeImpl._DEFAULT_IMPL = TypeImpl()


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

    def __init__(self, fields: dict[str, Type]):
        self.fields = fields

    def get(self, value: Value) -> str:
        return "null"

    def set(self, value: Value, source: Value):
        for field in self.fields.keys():
            value.getattr(field).set(source.getattr(field))

    def write(self, value: Value, cell: Value, index: Value):
        # TODO: serialization
        raise NotImplementedError

    def read(self, value: Value, cell: Value, index: Value):
        # TODO: deserialization
        raise NotImplementedError

    def getattr(self, value: Value, name: str) -> Value | None:
        if name in self.fields:
            return Value(self.fields[name], ABI.struct_field(value.value, name), value.const())

        return None


class FunctionTypeImpl(TypeImpl):
    params: list[tuple[Type, str]]
    ret: Type
    scope: dict[str, Value]

    def __init__(self, params: list[tuple[Type, str]], ret: Type, code, scope: dict[str, Value]):
        self.params = params
        self.ret = ret
        self.code = code
        self.scope = scope

    def callable(self, value: Value) -> bool:
        return True

    def call(self, value: Value, node, params: list[Value]) -> Value:
        for i, [type_, name] in enumerate(self.params):
            if params[i].type() not in type_:
                Error.incompatible_types(node, params[i].type(), type_)

            Value.variable(name, type_).set(params[i])

        self.code.gen()

        Gen.emit(
            InstructionSet(ABI.function_return(value.value), "null")
        )

        return Value(self.ret, ABI.function_return(value.value), False)

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
