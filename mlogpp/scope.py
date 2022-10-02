from .value import *
from .function import *
from . import constants


class Scope:
    """
    Scope, contains variable and function definitions.
    """

    name: str | None
    variables: set[VariableValue]
    functions: set[Function]

    def __init__(self, name: str | None, variables: set[VariableValue] | None = None, functions: set[Function] | None = None):
        self.name = name
        self.variables = variables if variables is not None else set()
        self.functions = functions if functions is not None else set()

    def add(self, var: VariableValue | Function) -> None:
        """
        Add a variable or function to the scope.

        Args:
            var: The variable or function to be added.
        """

        if isinstance(var, VariableValue):
            self.variables.add(var)
        elif isinstance(var, Function):
            self.functions.add(var)

    def remove(self, var: VariableValue | Function) -> None:
        """
        Remove a variable or function from scope.

        Args:
            var: The variable or function to be removed.
        """

        if isinstance(var, VariableValue):
            self.variables.remove(var)
        elif isinstance(var, Function):
            self.functions.remove(var)

    def rename(self, var: str) -> str:
        """
        Rename a variable with the scope name.

        Args:
            var: The variable to be renamed.

        Returns:
            The renamed variable.
        """

        if self.name is None:
            return var

        return f"__s_{self.name}_{var}"

    def get(self, name: str) -> VariableValue | Function | None:
        """
        Get a variable or function definition.

        Args:
            name: Name of the variable or function.

        Returns:
            The variable or function definition, None if nothing is found.
        """

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
    # the default scope, containing global constants and variables
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
    def reset() -> None:
        """
        Reset all the scopes.
        """

        Scopes.SCOPES = [Scopes.DEFAULT_SCOPE, Scope(None)]

    @staticmethod
    def push(name: str | None) -> None:
        """
        Push a scope to the stack.

        Args:
            name: Name of the scope to be pushed.
        """

        Scopes.SCOPES.append(Scope(name))

    @staticmethod
    def pop() -> None:
        """
        Pop a scope from the stack.
        """

        Scopes.SCOPES.pop(-1)

    @staticmethod
    def add(var: VariableValue | Function) -> None:
        """
        Add a variable or function to the top scope on the stack.

        Args:
            var: The variable or function to be added.
        """

        Scopes.SCOPES[-1].add(var)

    @staticmethod
    def remove(var: VariableValue | Function) -> None:
        """
        Remove a variable or function from the top scope on the stack.

        Args:
            var: The variable or function to be removed.
        """

        Scopes.SCOPES[-1].remove(var)

    @staticmethod
    def rename(var: str, declare: bool = False) -> str:
        """
        Rename a variable using the scope names.

        Args:
            var: The variable to be renamed.
            declare: If true, variable will be renamed using topmost scope, otherwise using first one that contains it.

        Returns:
            The renamed variable.
        """

        if declare:
            return Scopes.SCOPES[-1].rename(var)

        for scope in reversed(Scopes.SCOPES):
            if scope.rename(var) in scope:
                return scope.rename(var)

        return Scopes.SCOPES[0].rename(var)

    @staticmethod
    def get(name: str) -> VariableValue | Function | None:
        """
        Get a variable or function by name.

        Args:
            name: Name of the variable or function to be searched for.

        Returns:
            The variable or function, None if not found.
        """
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
