def sanitize(s: str) -> str:
    """
    sanitize a string
    """

    return s.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


class Position:
    """
    position in code
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
        generate error arrows
        """

        return f"{' ' * (self.start + 1)}{'^' * (self.end - self.start)}"
    
    def code_section(self) -> str:
        """
        get code section defined by the position
        """

        return self.code[self.start+1:self.end+1]
    
    def __add__(self, other: "Position") -> "Position":
        """
        create a range of two positions
        """

        if self.line == other.line:
            return Position(self.line, min(self.start, other.start), max(self.end, other.end), self.code, self.file)
        elif self.line < other.line:
            return Position(self.line, self.start, len(self.code), self.code, self.file)
        else:
            return Position(other.line, other.start, len(other.code), other.code, self.file)
    
    def __repr__(self) -> str:
        return f"Position({self.line}, {self.start}, {self.end}, \"{sanitize(self.code)}\", \"{sanitize(self.file)}\")"
