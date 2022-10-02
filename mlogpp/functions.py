import math

# precalculation functions
PRECALC = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b,
    "idiv": lambda a, b: a // b,
    "mod": lambda a, b: a % b,
    "pow": lambda a, b: a ** b,
    "not": lambda a, _: not a,
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
    "flip": lambda a, _: ~a,
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
    "sin": lambda a, _: math.sin(math.radians(a)),
    "cos": lambda a, _: math.cos(math.radians(a)),
    "tan": lambda a, _: math.tan(math.radians(a)),
    "asin": lambda a, _: math.degrees(math.asin(a)),
    "acos": lambda a, _: math.degrees(math.acos(a)),
    "atan": lambda a, _: math.degrees(math.atan(a))

    # noise and rand not implemented
    # equal and notEqual are not implemented because they use type conversion
}

# jump conditions for replacement optimization
JC_REPLACE = {
    "equal": "notEqual",
    "notEqual": "equal",
    "greaterThan": "lessThanEq",
    "lessThan": "greaterThanEq",
    "greaterThanEq": "lessThan",
    "lessThanEq": "greaterThan"
}
