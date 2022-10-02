from .value import *
from .function import *
from . import constants


class Scope:
    name: str | None
    variables: set[VariableValue]
    functions: set[Function]

    def __init__(self, name: str | None, variables: set[VariableValue] | None = None, functions: set[Function] | None = None):
        self.name = name
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

    def rename(self, var: str) -> str:
        if self.name is None:
            return var

        return f"__s_{self.name}_{var}"

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
    DEFAULT_SCOPE = Scope(
        None,
        {
            VariableValue(Type.BLOCK, "@this", True),
            VariableValue(Type.NUM, "@thisx", True),
            VariableValue(Type.NUM, "@thisy", True),
            VariableValue(Type.NUM, "@ipt", True),
            VariableValue(Type.NUM, "@counter"),
            VariableValue(Type.NUM, "@links", True),
            VariableValue(Type.UNIT, "@unit"),
            VariableValue(Type.NUM, "@time", True),
            VariableValue(Type.NUM, "@tick", True),
            VariableValue(Type.NUM, "@second", True),
            VariableValue(Type.NUM, "@minute", True),
            VariableValue(Type.NUM, "@waveNumber", True),
            VariableValue(Type.NUM, "@waveTime", True),
            VariableValue(Type.NUM, "@mapw", True),
            VariableValue(Type.NUM, "@maph", True),

            VariableValue(Type.NUM, "true", True),
            VariableValue(Type.NUM, "false", True),
            VariableValue(Type.NULL, "null", True),

            VariableValue(Type.CONTROLLER, "@ctrlProcessor", True),
            VariableValue(Type.CONTROLLER, "@ctrlPlayer", True),
            VariableValue(Type.CONTROLLER, "@ctrlCommand", True),

            VariableValue(Type.BLOCK_TYPE, "@solid", True)
        } | {
            VariableValue(Type.BLOCK_TYPE, "@" + block, True) for block in constants.BLOCKS
        } | {
            VariableValue(Type.ITEM_TYPE, "@" + item, True) for item in constants.ITEMS
        } | {
            VariableValue(Type.LIQUID_TYPE, "@" + liquid, True) for liquid in constants.LIQUIDS
        } | {
            VariableValue(Type.TEAM, "@" + team, True) for team in constants.TEAMS
        }
    )

    SCOPES = [DEFAULT_SCOPE, Scope(None)]

    @staticmethod
    def reset():
        Scopes.SCOPES = [Scopes.DEFAULT_SCOPE, Scope(None)]

    @staticmethod
    def push(name: str | None):
        Scopes.SCOPES.append(Scope(name))

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
    def rename(var: str, declare: bool = False) -> str:
        if declare:
            return Scopes.SCOPES[-1].rename(var)

        for scope in reversed(Scopes.SCOPES):
            if scope.rename(var) in scope:
                return scope.rename(var)

        return Scopes.SCOPES[0].rename(var)

    @staticmethod
    def get(name: str) -> VariableValue | Function | None:
        for scope in reversed(Scopes.SCOPES):
            if (var := scope.get(name)) is not None:
                return var

        return None

    @staticmethod
    def __len__(self) -> int:
        return len(Scopes.SCOPES)

    @staticmethod
    def __contains__(item: VariableValue | Function | str) -> bool:
        for scope in Scopes.SCOPES:
            if item in scope:
                return True

        return False
