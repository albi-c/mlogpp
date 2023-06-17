from .error import Error
from .values import Type, Value
from .generator import Gen
from .builtins import BUILTINS


class Scope:
    scopes: list[dict[str, Value]] = [BUILTINS, {}]

    @classmethod
    def push(cls):
        cls.scopes.append({})

    @classmethod
    def pop(cls):
        cls.scopes.pop(-1)

    @classmethod
    def reset(cls):
        cls.scopes = [BUILTINS, {}]

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
    def declare(cls, node: 'Node', name: str, value: Value):
        scope = cls._find(node, name, False)

        if scope is None:
            cls.scopes[-1][name] = value

        else:
            Error.already_defined_var(node, name)

    @classmethod
    def _find(cls, node: 'Node', name: str, error: bool) -> dict[str, Value] | None:
        for scope in reversed(cls.scopes):
            print(scope)
            if name in scope:
                return scope

        if error:
            Error.undefined_variable(node, name)

        return None
