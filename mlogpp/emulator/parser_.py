import shlex, math, random, re

from .building import EBuilding, EBuildingType

REGEX_NUM = re.compile(r"^[0-9]+(\.[0-9]+)?$")

INSTRUCTIONS = {
    "read": 3,
    "write": 3,
    "draw": 7,
    "print": 1,
    "drawflush": 1,
    "printflush": 1,
    "getlink": 2,
    "control": 6,
    "radar": 7,
    "sensor": 3,
    "set": 2,
    "op": 4,
    "end": 0,
    "jump": 4,
    "ubind": 1,
    "ucontrol": 6,
    "uradar": 7,
    "ulocate": 8
}

UNSUPPORTED_INSTRUCTIONS = [
    "draw", "drawflush", "getlink", "control", "radar", "sensor", "ubind", "ucontrol", "uradar", "ulocate"
]

OPERATORS = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b,
    "idiv": lambda a, b: a // b,
    "mod": lambda a, b: a % b,
    "pow": lambda a, b: a ** b,
    "equal": lambda a, b: a == b,
    "notEqual": lambda a, b: a != b,
    "land": lambda a, b: a and b,
    "lessThan": lambda a, b: a < b,
    "lessThanEq": lambda a, b: a <= b,
    "greaterThan": lambda a, b: a > b,
    "greaterThanEq": lambda a, b: a >= b,
    "strictEqual": lambda a, b: a == b,
    "shl": lambda a, b: a << b,
    "shr": lambda a, b: a >> b,
    "or": lambda a, b: a | b,
    "and": lambda a, b: a & b,
    "xor": lambda a, b: a ^ b,
    "not": lambda a, _: ~a,
    "max": lambda a, b: max(a, b),
    "min": lambda a, b: min(a, b),
    "abs": lambda a, _: abs(a),
    "log": lambda a, _: math.log(a),
    "log10": lambda a, _: math.log10(a),
    "floor": lambda a, _: math.floor(a),
    "ceil": lambda a, _: math.ceil(a),
    "sqrt": lambda a, _: math.sqrt(a),
    "angle": lambda a, b: math.atan2(b, a) * 180 / math.pi,
    "length": lambda a, b: math.sqrt(a * a + b * b),
    "noise": lambda a, b: (random.randint(0, 2000) - 1000) / 1000,
    "rand": lambda a, _: random.randint(0, a),
    "sin": lambda a, _: math.sin(a),
    "cos": lambda a, _: math.cos(a),
    "tan": lambda a, _: math.tan(a),
    "asin": lambda a, _: math.asin(a),
    "acos": lambda a, _: math.acos(a),
    "atan": lambda a, _: math.atan(a)
}

JUMP_CONDITIONS = {
    "equal": lambda a, b: a == b,
    "notEqual": lambda a, b: a != b,
    "lessThan": lambda a, b: a < b,
    "lessThanEq": lambda a, b: a <= b,
    "greaterThan": lambda a, b: a > b,
    "greaterThanEq": lambda a, b: a >= b,
    "strictEqual": lambda a, b: a == b,
    "always": lambda a, b: True
}

class EParserException(Exception):
    pass

class EExecutionError(Exception):
    pass

class EInstruction:
    def __init__(self, name: str, params: list = None):
        self.name = name
        self.params = params if params is not None else []
    
    def __repr__(self) -> str:
        params_list = [f"\"{p}\"" for p in self.params]
        return f"EInstruction(\"{self.name}\", [{', '.join(params_list)}])"
    
    def resolve_value(self, value: any, env: dict) -> any:
        if REGEX_NUM.fullmatch(value):
            return float(value)
        
        if type(value) == str:
            if value.startswith("\""):
                if value.endswith("\""):
                    return value[1:-1]
                else:
                    raise EExecutionError(f"Invalid string {value}")
            else:
                if value in env["variables"]:
                    return env["variables"][value]
                else:
                    raise EExecutionError(f"Undefined variable \"{value}\"")

        return value
    
    def execute(self, env: dict):
        if self.name == "read":
            target = self.params[0]
            cell = self.resolve_value(self.params[1], env)
            pos = self.resolve_value(self.params[2], env)

            if type(cell) != EBuilding or cell.type != EBuildingType.CELL:
                raise EExecutionError(f"Invalid memory cell \"{cell}\"")
            
            try:
                pos = int(pos)
            except ValueError:
                raise EExecutionError(f"Invalid memory cell position \"{pos}\"")
            
            if pos >= cell["params"]["size"]:
                raise EExecutionError(f"Memory cell access out of bounds {pos}")

            env["variables"][target] = cell["state"]["memory"][pos]
        elif self.name == "write":
            value = self.resolve_value(self.params[0], env)
            cell = self.resolve_value(self.params[1], env)
            pos = self.resolve_value(self.params[2], env)

            try:
                value = float(value)
            except ValueError:
                raise EExecutionError(f"Invalid data to write into memory cell \"{pos}\"")

            if type(cell) != EBuilding or cell.type != EBuildingType.CELL:
                raise EExecutionError(f"Invalid memory cell \"{cell}\"")
            
            try:
                pos = int(pos)
            except ValueError:
                raise EExecutionError(f"Invalid memory cell position \"{pos}\"")
            
            if pos >= cell["params"]["size"]:
                raise EExecutionError(f"Memory cell access out of bounds {pos}")
            
            cell["state"]["memory"][pos] = value
        elif self.name == "draw":
            pass
        elif self.name == "print":
            value = self.resolve_value(self.params[0], env)

            env["print_buffer"] += str(value)
        elif self.name == "drawflush":
            pass
        elif self.name == "printflush":
            message = self.resolve_value(self.params[0], env)

            if type(message) != EBuilding or message.type != EBuildingType.MESSAGE:
                raise EExecutionError(f"Invalid message \"{message}\"")
            
            message.state["text"] = env["print_buffer"]
            env["print_buffer"] = ""
        elif self.name == "getlink":
            pass
        elif self.name == "control":
            pass
        elif self.name == "radar":
            pass
        elif self.name == "sensor":
            pass
        elif self.name == "set":
            var = self.params[0]
            value = self.resolve_value(self.params[1], env)

            env["variables"][var] = value
        elif self.name == "op":
            op = self.params[0]
            out = self.params[1]
            a = self.resolve_value(self.params[2], env)
            b = self.resolve_value(self.params[3], env)

            if op not in OPERATORS:
                raise EExecutionError(f"Invalid operator \"{op}\"")
            
            try:
                if a not in  [None, True, False]:
                    a = float(a)
            except ValueError:
                raise EExecutionError(f"Invalid operation input [a] \"{a}\"")
            
            try:
                if b not in  [None, True, False]:
                    b = float(b)
            except ValueError:
                raise EExecutionError(f"Invalid operation input [b] \"{b}\"")
            
            env["variables"][out] = OPERATORS[op](a, b)
        elif self.name == "end":
            env["variables"]["@counter"] = 0
        elif self.name == "jump":
            pos = self.params[0]
            try:
                pos = int(pos)
            except ValueError:
                raise EExecutionError(f"Invalid jump destination \"{pos}\"")
            
            cond = self.params[1]
            a = self.resolve_value(self.params[2], env)
            b = self.resolve_value(self.params[2], env)

            if cond not in JUMP_CONDITIONS:
                raise EExecutionError(f"Invalid jump condition \"{cond}\"")

            try:
                if a not in  [None, True, False]:
                    a = float(a)
            except ValueError:
                raise EExecutionError(f"Invalid jump input [a] \"{a}\"")
            
            try:
                if b not in  [None, True, False]:
                    b = float(b)
            except ValueError:
                raise EExecutionError(f"Invalid jump input [b] \"{b}\"")
            
            if JUMP_CONDITIONS[cond](a, b):
                env["variables"]["@counter"] = pos
        elif self.name == "ubind":
            pass
        elif self.name == "ucontrol":
            pass
        elif self.name == "uradar":
            pass
        elif self.name == "ulocate":
            pass

class EParser:
    def __init__(self):
        pass

    def parse(self, code: str) -> list:
        tmp = []

        for ln in code.splitlines():
            if not ln.strip():
                continue
            
            spl = shlex.split(ln, comments = False, posix = False)

            if len(spl) > 0:
                if spl[0] in INSTRUCTIONS:
                    if INSTRUCTIONS[spl[0]] != len(spl) - 1:
                        raise EParserException(f"Incorrect number of parameters to instructions ({len(spl) - 1}, expected {INSTRUCTIONS[spl[0]]})")
                    
                    if spl[0] in UNSUPPORTED_INSTRUCTIONS:
                        print(f"WARNING: you are using an unsupported instruction ({spl[0]})")
                    
                    tmp.append(EInstruction(spl[0], spl[1:] if len(spl) > 1 else []))
                else:
                    raise EParserException(f"Invalid instruction \"{spl[0]}\"")
        
        print(tmp)
        return tmp