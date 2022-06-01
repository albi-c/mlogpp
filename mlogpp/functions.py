# native functions
native = {
    "read": 3, "write": 3,
    "drawflush": 1,
    "print": 1, "printflush": 1,
    "getlink": 2,
    "radar": 6,
    "sensor": 3,
    "set": 2, "op": 4,
    "wait": 1,
    "end": 0, "jump": 4,
    "ubind": 1, "uradar": 6
}

# return positions for native functions
native_ret = {
    "read": 0,
    "getlink": 0,
    "radar": 6,
    "sensor": 0,
    "uradar": 6,
    "op": 1
}

# native subcommands
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
    },
    "lookup": {
        "block": 2,
        "unit": 2,
        "item": 2,
        "liquid": 2
    },
    "ulocate": {
        "ore": 1,
        "building": 2,
        "spawn": 0,
        "damaged": 0
    }
}

# generate list of native subcommand combinations
native_sublist = []
for k, v in native_sub.items():
    for s in v.keys():
        native_sublist.append(f"{k}.{s}")

# native subcommands return positions
native_sub_ret = {
    "ucontrol.getBlock": (2,),
    "ucontrol.within": (3,),

    "lookup.block": (0,),
    "lookup.unit": (0,),
    "lookup.item": (0,),
    "lookup.liquid": (0,),

    "ulocate.ore": (3, 4, 5, 6),
    "ulocate.building": (3, 4, 5, 6),
    "ulocate.spawn": (3, 4, 5, 6),
    "ulocate.damaged": (3, 4, 5, 6)
}

# builtin operators
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

# number of parameters to builtin operators
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

# special keywords with parentheses
keywords_paren = ["if", "while", "for", "function", "repeat"]

# special keywords
keywords = ["if", "else", "while", "for", "function", "repeat"]

# special identifiers
special = list(native.keys()) + builtin + keywords
