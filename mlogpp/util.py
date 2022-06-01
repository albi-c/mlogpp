def sanitize(s: str) -> str:
    """
    sanitize a string
    """

    return s.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")

class Position:
    """
    position in code
    """
    
    def __init__(self, line: int, start: int, end: int, code: str):
        self.line = line + 1
        self.start = start + 1
        self.end = end + 1
        self.code = sanitize(code)
    
    def arrows(self) -> str:
        """
        generate error arrows
        """

        return f"{' ' * (self.start - 1)}{'^' * (self.end - self.start)}"
    
    def __add__(self, other: "Position") -> "Position":
        """
        create a range of two positions
        """

        if self.line == other.line:
            return Position(self.line - 1, min(self.start, other.start) - 1, max(self.end, other.end) - 1, self.code)
        elif self.line < other.line:
            return Position(self.line - 1, self.start - 1, len(self.code) - 1, self.code)
        else:
            return Position(other.line - 1, other.start - 1, len(other.code) - 1, other.code)
    
    def __repr__(self) -> str:
        return f"Position({self.line - 1}, {self.start - 1}, {self.end - 1}, \"{sanitize(self.code)}\")"
