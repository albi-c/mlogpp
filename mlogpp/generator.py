import re


class Var:
    """
    variable class
    """

    n: str
    c: bool
    nc: bool

    def __init__(self, name: str, can_edit: bool = False):
        self.n = name
        self.c = can_edit
        self.nc = not self.c
    
    def __str__(self) -> str:
        return self.n
    
    def e(self, can_edit: bool = False) -> 'Var':
        """
        create a copy with different edit flag
        """

        return Var(self.n, can_edit)


class Gen:
    """
    generates temporary values, stores generation regexes
    """

    VAR_COUNT = 0
    LAB_COUNT = 0

    GLOBALS_STACK = []

    REGEXES = {
        "ATTR": re.compile(r"^[a-zA-Z_@][a-zA-Z0-9_]*\.[a-zA-Z_@][a-zA-Z0-9_]*$")
    }

    @staticmethod
    def reset():
        """
        reset the generator
        """

        Gen.VAR_COUNT = 0
        Gen.LAB_COUNT = 0

        Gen.GLOBALS_STACK = []

    @staticmethod
    def temp_var(_: Var | str | None = None) -> Var:
        """
        generate a temporary variable
        """

        Gen.VAR_COUNT += 1
        return Var(f"__tmp{Gen.VAR_COUNT-1}", True)
    
    @staticmethod
    def temp_lab() -> str:
        """
        generate a temporary label
        """

        Gen.LAB_COUNT += 1
        return f"__tmp{Gen.LAB_COUNT-1}"
    
    @staticmethod
    def is_global(name: str) -> bool:
        if len(Gen.GLOBALS_STACK) > 0:
            return name in Gen.GLOBALS_STACK[-1]
        return False
    
    @staticmethod
    def push_globals():
        Gen.GLOBALS_STACK.append(set())
    
    @staticmethod
    def pop_globals():
        Gen.GLOBALS_STACK.pop(-1)
    
    @staticmethod
    def add_globals(global_variables: list):
        Gen.GLOBALS_STACK[-1] |= set(global_variables)
