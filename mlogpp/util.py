def sanitize(s: str) -> str:
    """
    Sanitize a string.

    Args:
        s: The string to be sanitized.

    Returns:
        The sanitized string.
    """

    return s.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


def flatten(lst: list[list]) -> list:
    """
    Flatten a two-dimensional list.

    Args:
        lst: The list to be flattened.

    Returns:
        The flattened list.
    """

    return [item for sublist in lst for item in sublist]


class Position:
    """
    Position in code.
    """

    line: int
    start: int
    end: int
    code: str
    file: str
    
    def __init__(self, line: int, start: int, end: int, code: str, file: str):
        self.line = line
        self.start = start
        self.end = end
        self.code = sanitize(code)
        self.file = file
    
    def arrows(self) -> str:
        """
        Generate error arrows for the position.

        Returns:
            The generated arrows.
        """

        return f"{' ' * self.start}{'^' * (self.end - self.start)}"
    
    def code_section(self) -> str:
        """
        Get the code section in the position.

        Returns:
            The code section in the position.
        """

        return self.code[self.start:self.end]
    
    def __add__(self, other: "Position") -> "Position":
        """
        Create a range of two positions.
        """

        if self.line == other.line:
            return Position(self.line, min(self.start, other.start), max(self.end, other.end), self.code, self.file)
        elif self.line < other.line:
            return Position(self.line, self.start, len(self.code), self.code, self.file)
        else:
            return Position(other.line, other.start, len(other.code), other.code, self.file)

    def __iadd__(self, other: "Position") -> "Position":
        """
        Create a range of two positions.
        """

        if self.line == other.line:
            self.start = min(self.start, other.start)
            self.end = max(self.end, other.end)
        elif self.line < other.line:
            self.end = len(self.code)
        else:
            self.line = other.line
            self.start = other.start
            self.end = len(other.code)
            self.code = other.code
    
    def __repr__(self) -> str:
        return f"Position({self.line}, {self.start}, {self.end}, \"{sanitize(self.code)}\", \"{sanitize(self.file)}\")"
