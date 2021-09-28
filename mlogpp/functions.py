def gen_signature(name: str, params: list):
    return f"{name}:{len(params)}"

native = [
    "read", "write",
    "draw", "drawflush",
    "print", "printflush",
    "getlink",
    "control",
    "radar",
    "sensor",
    "set", "op",
    "wait", "lookup",
    "end", "jump",
    "ubind", "ucontrol", "uradar", "ulocate"
]

native_params = {
    "read": 3, "write": 3,
    "draw": 7, "drawflush": 1,
    "print": 1, "printflush": 1,
    "getlink": 2,
    "control": 6,
    "radar": 6,
    "sensor": 3,
    "set": 2, "op": 4,
    "wait": 1, "lookup": 3,
    "end": 0, "jump": 4,
    "ubind": 1, "ucontrol":6, "uradar": 6, "ulocate": 8
}

builtin = [
    "mod",
    "pow",
    "and", "or", "xor", "not",
    "max", "min",
    "abs",
    "log", "log10",
    "ceil", "floor",
    "sqrt",
    "sin", "cos", "tan",
    "asin", "acos", "atan"
]

builtin_params_default = 1
builtin_params = {
    "mod": 2,
    "pow": 2,
    "and": 2,
    "or": 2,
    "xor": 2,
    "max": 2,
    "min": 2
}

keywords = ["if", "else", "while", "for", "function", "repeat"]

special = native + builtin + keywords
