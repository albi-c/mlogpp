from .value import *


class Gen:
    """
    Generates unnamed values.
    """

    VAR_COUNT = 0
    LAB_COUNT = 0
    SCOPE_COUNT = 0

    @staticmethod
    def reset():
        """
        reset the generator
        """

        Gen.VAR_COUNT = 0
        Gen.LAB_COUNT = 0
        Gen.SCOPE_COUNT = 0

    @staticmethod
    def temp_var(type_: Type) -> VariableValue:
        """
        generate a temporary variable
        """

        Gen.VAR_COUNT += 1
        return VariableValue(type_, f"__tmp{Gen.VAR_COUNT-1}")
    
    @staticmethod
    def temp_lab() -> str:
        """
        generate a temporary label
        """

        Gen.LAB_COUNT += 1
        return f"__tmp{Gen.LAB_COUNT-1}"

    @staticmethod
    def scope_name() -> str:
        """
        generate a scope name
        """

        Gen.SCOPE_COUNT += 1
        return f"s{Gen.SCOPE_COUNT}"
