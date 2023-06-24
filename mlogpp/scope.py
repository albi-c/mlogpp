from .error import Error
from .values import Value
from .abi import ABI
from .instruction import Instruction, InstructionSet


class Scope:
    scopes: list[dict[str, Value]] = []
    names: list[str] = []
    functions: list[str] = []
    loops: list[str] = []
    configurations: dict[str, Value] = []

    @classmethod
    def push(cls, name: str):
        cls.scopes.append({})
        cls.names.append(name)

        if ABI.is_function(name):
            cls.functions.append(name)

        if ABI.is_loop(name):
            cls.loops.append(name)

    @classmethod
    def pop(cls):
        cls.scopes.pop(-1)
        name = cls.names.pop(-1)

        if ABI.is_function(name):
            cls.functions.pop(-1)

        if ABI.is_loop(name):
            cls.loops.pop(-1)

    @classmethod
    def enum(cls, data: dict[str, Value] | None = None):
        cls.scopes[0] = data if data is not None else {}

    @classmethod
    def reset(cls, builtins: dict[str, Value]):
        cls.scopes = [{}, builtins, {}, {}]
        cls.names = ["<enum>", "<builtins>", "<config>", "<main>"]
        cls.functions = []
        cls.loops = []
        cls.configurations = {}

    @classmethod
    def get_config(cls) -> list[Instruction]:
        return [InstructionSet(name, value.get()) for name, value in cls.configurations.items()]

    @classmethod
    def name(cls) -> str:
        return cls.names[-1]

    @classmethod
    def function(cls) -> str | None:
        return cls.functions[-1] if len(cls.functions) > 0 else None

    @classmethod
    def loop(cls) -> str | None:
        return cls.loops[-1] if len(cls.loops) > 0 else None

    @classmethod
    def get(cls, node, name: str) -> Value:
        scope = cls._find(node, name, True)

        return scope[name]

    @classmethod
    def set(cls, node, name: str, value: Value):
        scope = cls._find(node, name, False)

        if scope is None:
            cls.scopes[-1][name] = value

        else:
            if scope[name].type() != value.type():
                Error.undefined_variable(node, name)

            scope[name] = value

    @classmethod
    def delete(cls, node, name: str):
        scope = cls._find(node, name, True)

        del scope[name]

    @classmethod
    def declare(cls, node, name: str, value: Value) -> str:
        if name in cls.scopes[-1]:
            Error.already_defined_var(node, name)

        else:
            cls.scopes[-1][name] = value
            return f"{name}@{cls.names[-1]}"

    @classmethod
    def _find(cls, node, name: str, error: bool) -> dict[str, Value] | None:
        for scope in reversed(cls.scopes):
            if name in scope:
                return scope

        if error:
            Error.undefined_variable(node, name)

        return None
