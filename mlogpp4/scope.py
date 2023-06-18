from .error import Error
from .values import Type, Value
from .generator import Gen
from .builtins import BUILTINS
from .abi import ABI


class Scope:
    scopes: list[dict[str, Value]] = [BUILTINS, {}]
    names: list[str] = ["<builtins>", "<main>"]
    functions: list[str] = []
    loops: list[str] = []

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
    def reset(cls):
        cls.scopes = [BUILTINS, {}]
        cls.names = ["<builtins>", "<main>"]
        cls.functions = []
        cls.loops = []

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
    def get(cls, node: 'Node', name: str) -> Value:
        scope = cls._find(node, name, True)

        return scope[name]

    @classmethod
    def set(cls, node: 'Node', name: str, value: Value):
        scope = cls._find(node, name, False)

        if scope is None:
            cls.scopes[-1][name] = value

        else:
            if scope[name].type() != value.type():
                Error.undefined_variable(node, name)

            scope[name] = value

    @classmethod
    def delete(cls, node: 'Node', name: str):
        scope = cls._find(node, name, True)

        del scope[name]

    @classmethod
    def declare(cls, node: 'Node', name: str, value: Value) -> str:
        scope = cls._find(node, name, False)

        if scope is None:
            cls.scopes[-1][name] = value
            return f"{name}@{cls.names[-1]}"

        else:
            Error.already_defined_var(node, name)

    @classmethod
    def _find(cls, node: 'Node', name: str, error: bool) -> dict[str, Value] | None:
        for scope in reversed(cls.scopes):
            if name in scope:
                return scope

        if error:
            Error.undefined_variable(node, name)

        return None
