from .value import *
from .function import *
from . import constants


class Scope:
    variables: set[VariableValue]
    functions: set[Function]

    def __init__(self, variables: set[VariableValue] | None = None, functions: set[Function] | None = None):
        self.variables = variables if variables is not None else set()
        self.functions = functions if functions is not None else set()

    def add(self, var: VariableValue | Function):
        if isinstance(var, VariableValue):
            self.variables.add(var)
        elif isinstance(var, Function):
            self.functions.add(var)

    def remove(self, var: VariableValue | Function):
        if isinstance(var, VariableValue):
            self.variables.remove(var)
        elif isinstance(var, Function):
            self.functions.remove(var)

    def get(self, name: str) -> VariableValue | Function | None:
        for var in self.variables:
            if var.name == name:
                return var

        for fun in self.functions:
            if fun.name == name:
                return fun

        return None

    def __contains__(self, var: VariableValue | Function | str):
        if isinstance(var, VariableValue):
            return var in self.variables

        elif isinstance(var, Function):
            return var in self.functions

        return any(var_.name == var for var_ in self.variables) or any(fun.name == var for fun in self.functions)


class Scopes:
    SCOPES = [Scope({
        VariableValue(Type.BLOCK, "@this", False),
        VariableValue(Type.NUM, "@thisx", False),
        VariableValue(Type.NUM, "@thisy", False),
        VariableValue(Type.NUM, "@ipt", False),
        VariableValue(Type.NUM, "@counter"),
        VariableValue(Type.NUM, "@links", False),
        VariableValue(Type.UNIT, "@unit"),
        VariableValue(Type.NUM, "@time", False),
        VariableValue(Type.NUM, "@tick", False),
        VariableValue(Type.NUM, "@second", False),
        VariableValue(Type.NUM, "@minute", False),
        VariableValue(Type.NUM, "@waveNumber", False),
        VariableValue(Type.NUM, "@waveTime", False),
        VariableValue(Type.NUM, "@mapw", False),
        VariableValue(Type.NUM, "@maph", False),

        VariableValue(Type.NUM, "true", False),
        VariableValue(Type.NUM, "false", False),
        VariableValue(Type.NULL, "null", False),

        VariableValue(Type.CONTROLLER, "@ctrlProcessor", False),
        VariableValue(Type.CONTROLLER, "@ctrlPlayer", False),
        VariableValue(Type.CONTROLLER, "@ctrlCommand", False),

        VariableValue(Type.TEAM, "@derelict", False),
        VariableValue(Type.TEAM, "@sharded", False),
        VariableValue(Type.TEAM, "@crux", False),
        VariableValue(Type.TEAM, "@malis", False),
        VariableValue(Type.TEAM, "@green", False),
        VariableValue(Type.TEAM, "@blue", False),

        VariableValue(Type.BLOCK_TYPE, "@solid", False)
    } | {
        VariableValue(type_, name, False) for name, type_ in constants.SENSOR_READABLE.items()
    })]

    @staticmethod
    def push():
        Scopes.SCOPES.append(Scope())

    @staticmethod
    def pop():
        Scopes.SCOPES.pop(-1)

    @staticmethod
    def add(var: VariableValue | Function):
        Scopes.SCOPES[-1].add(var)

    @staticmethod
    def remove(var: VariableValue | Function):
        Scopes.SCOPES[-1].remove(var)

    @staticmethod
    def get(name: str) -> VariableValue | Function | None:
        for scope in reversed(Scopes.SCOPES):
            if (var := scope.get(name)) is not None:
                return var

        return None

    @staticmethod
    def __len__(self):
        return len(Scopes.SCOPES)

    @staticmethod
    def __getitem__(item: int):
        return Scopes.SCOPES[i]

    @staticmethod
    def __contains__(self, item: VariableValue | Function | str):
        for scope in Scopes.SCOPES:
            if item in scope:
                return True

        return False
