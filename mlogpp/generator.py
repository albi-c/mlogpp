from .value import *


class Gen:
    """
    generates temporary values, stores compile time values
    """

    VAR_COUNT = 0
    LAB_COUNT = 0

    LOCALS_STACK = []

    @staticmethod
    def reset():
        """
        reset the generator
        """

        Gen.VAR_COUNT = 0
        Gen.LAB_COUNT = 0

        Gen.LOCALS_STACK = []

    @staticmethod
    def temp_var(type_: Type, var: Value | None = None) -> Value:
        """
        generate a temporary variable
        """

        if var is not None and var.writable:
            return var

        Gen.VAR_COUNT += 1
        return VariableValue(type_, "__tmp{Gen.VAR_COUNT-1}", True)
    
    @staticmethod
    def temp_lab() -> str:
        """
        generate a temporary label
        """

        Gen.LAB_COUNT += 1
        return f"__tmp{Gen.LAB_COUNT-1}"
    
    @staticmethod
    def is_local(name: str) -> bool:
        if len(Gen.LOCALS_STACK) > 0:
            return name in Gen.LOCALS_STACK[-1]
        return False
    
    @staticmethod
    def push_locals():
        Gen.LOCALS_STACK.append(set())
    
    @staticmethod
    def pop_locals():
        Gen.LOCALS_STACK.pop(-1)
    
    @staticmethod
    def add_locals(locals_variables: list):
        Gen.LOCALS_STACK[-1] |= set(locals_variables)
