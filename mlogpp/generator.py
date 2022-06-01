import re

class Var:
    """
    variable class
    """

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

        return Var(self.name, can_edit)

class Gen:
    """
    generates temporary values, stores generation regexes
    """

    VAR_COUNT = 0
    LAB_COUNT = 0

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

    @staticmethod
    def temp_var(v: Var = None):
        """
        generate a temporary variable
        """

        # if v is not None and v.c:
        #     return v

        Gen.VAR_COUNT += 1
        return Var(f"__tmp{Gen.VAR_COUNT-1}", True)
    
    @staticmethod
    def temp_lab():
        """
        generate a temporary variable
        """

        Gen.LAB_COUNT += 1
        return f"__tmp{Gen.LAB_COUNT-1}"
