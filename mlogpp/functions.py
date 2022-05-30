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

native_sub = {
    "draw": {
        "clear": 3,
        "color": 4,
        "stroke": 1,
        "line": 4,
        "rect": 4,
        "lineRect": 4,
        "poly": 5,
        "linePoly": 5,
        "triangle": 6,
        "image": 5
    },
    "control": {
        "enabled": 2,
        "shoot": 4,
        "shootp": 3,
        "config": 2,
        "color": 4
    },
    "ucontrol": {
        "idle": 0,
        "stop": 0,
        "move": 2,
        "approach": 3,
        "boost": 1,
        "pathfind": 0,
        "target": 3,
        "targetp": 2,
        "itemDrop": 2,
        "itemTake": 3,
        "payDrop": 0,
        "payTake": 1,
        "payEnter": 0,
        "mine": 2,
        "flag": 1,
        "build": 5,
        "getBlock": 4,
        "within": 4
    }
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
    "asin", "acos", "atan",
    "len"
]

builtin_params_default = 1
builtin_params = {
    "mod": 2,
    "pow": 2,
    "and": 2,
    "or": 2,
    "xor": 2,
    "max": 2,
    "min": 2,
    "len": 2
}

keywords = ["if", "else", "while", "for", "function", "repeat"]

special = native + builtin + keywords
