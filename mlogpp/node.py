from .util import Position
from .error import gen_error
from .generator import Gen, Var
from .instruction import *
from . import functions


class Node:
    """
    base node class
    """

    def __init__(self, pos: Position):
        self.pos = pos

    def get_pos(self) -> Position:
        return self.pos

    def generate(self) -> Instructions | Instruction:
        return Instructions()

    def get(self) -> tuple[Instructions | Instruction, str | Var]:
        return Instructions(), ""

    def set(self) -> tuple[Instructions | Instruction, str | Var]:
        return Instructions(), ""

    def table_rename(self, _: dict):
        return self

    def function_rename(self, _: str):
        return self


class CodeListNode(Node):
    """
    node with a list of code
    """

    def __init__(self, pos: Position, code: list):
        super().__init__(pos)

        self.code = code

    def get_pos(self) -> Position:
        if len(self.code) > 0:
            return self.pos + self.code[-1].get_pos()

        return self.pos

    def generate(self):
        ins = Instructions()
        for node in self.code:
            ins += node.generate()
        return ins

    def table_rename(self, variables: dict):
        return CodeListNode(self.pos, [c.table_rename(variables) for c in self.code])

    def function_rename(self, name: str):
        return CodeListNode(self.pos, [c.function_rename(name) for c in self.code])


class ReturnNode(Node):
    """
    function return node
    """

    def __init__(self, pos: Position, func: str, value: Node):
        super().__init__(pos)

        self.func = func
        self.value = value

    def get_pos(self) -> Position:
        return self.value.get_pos()

    def generate(self):
        valc, valv = self.value.get()
        return valc + MInstruction(MInstructionType.SET, [f"__f_{self.func}_retv", valv])

    def table_rename(self, variables: dict):
        return ReturnNode(self.pos, self.func, self.value.table_rename(variables))

    def function_rename(self, name: str):
        return ReturnNode(self.pos, self.func, self.value.function_rename(name))


class LoopActionNode(Node):
    ACTIONS = ["break", "continue"]

    def __init__(self, pos: Position, name: str, action: str):
        super().__init__(pos)

        self.name = name
        self.action = action

    def get_pos(self) -> Position:
        return self.pos

    def generate(self):
        if self.action == "break":
            return MppInstructionJump(f"{self.name}_e")
        elif self.action == "continue":
            return MppInstructionJump("{self.name}_s")


class AssignmentNode(Node):
    OPERATORS = {
        "+=": "add",
        "-=": "sub",
        "*=": "mul",
        "/=": "div",
        "//=": "idiv",
        "%=": "mod",
        "&=": "and",
        "|=": "or",
        "^=": "xor",
        "<<=": "shl",
        ">>=": "shr"
    }

    def __init__(self, pos: Position, var: Node, op: str, value: Node):
        super().__init__(pos)

        self.var = var
        self.op = op
        self.value = value

    def get_pos(self) -> Position:
        return self.pos + self.value.get_pos()

    def generate(self):
        if self.op == "=":
            varc, varv = self.var.set()
            valc, valv = self.value.get()
            return valc + MInstruction(MInstructionType.SET, [varv, valv]) + varc

        else:
            # determine operator
            op = AssignmentNode.OPERATORS.get(self.op)
            if op is None:
                gen_error(self.get_pos(), f"Invalid operator: \"{self.op}\"")

            vasc, vasv = self.var.get()
            varc, varv = self.var.set()
            valc, valv = self.value.get()
            return vasc + valc + MInstruction(MInstructionType.OP, [op, varv, vasv, valv]) + varc

    def table_rename(self, variables: dict):
        return AssignmentNode(self.pos, self.var.table_rename(variables), self.op, self.value.table_rename(variables))

    def function_rename(self, name: str):
        return AssignmentNode(self.pos, self.var.function_rename(name), self.op, self.value.function_rename(name))


class CallNode(Node):
    def __init__(self, pos: Position, func: str, args: list):
        super().__init__(pos)

        self.func = func
        self.args = args

        self._ret_var = "_"

    def get_pos(self) -> Position:
        if len(self.args) > 0:
            return self.pos + self.args[-1].get_pos()

        return self.pos

    def generate(self):
        if self.func in functions.native:
            nargs = functions.native[self.func]
            return_var = "_"
            if self.func in functions.native_ret:
                nargs -= 1
                return_var = Gen.temp_var()

            if len(self.args) != nargs:
                gen_error(self.get_pos(),
                          f"Invalid number of arguments to function \"{self.func}\" (expected {nargs}, got {len(self.args)})")

            code = Instructions()
            args = []
            for a in self.args:
                ac, av = a.get()
                code += ac
                args.append(av)
            if self.func in functions.native_ret:
                args.insert(functions.native_ret[self.func], return_var)
                self._ret_var = return_var
            else:
                self._ret_var = "_"

            try:
                return code + MInstruction(MInstructionType[self.func.upper()], list(map(str, args)))
            except KeyError:
                gen_error(self.get_pos(), f"Invalid native function \"{self.func}\"")

        elif self.func in functions.native_sublist:
            spl = self.func.split(".")

            nargs = functions.native_sub[spl[0]][spl[1]]
            return_var = "_"
            if self.func in functions.native_sub_ret:
                nargs -= 1
                return_var = Gen.temp_var()
            self._ret_var = return_var

            if len(self.args) != nargs:
                gen_error(self.get_pos(),
                          f"Invalid number of arguments to function \"{self.func}\" (expected {nargs}, got {len(self.args)})")

            code = Instructions()
            args = []
            for a in self.args:
                ac, av = a.get()
                code += ac
                args.append(av)

            if return_var != "_":
                args.insert(functions.native_sub_ret[self.func], return_var)

            try:
                return code + MInstruction(MInstructionType[spl[0].upper()], [spl[1]] + list(map(str, args)))
            except KeyError:
                gen_error(self.get_pos(), f"Invalid native function \"{self.func}\"")

        elif self.func in functions.builtin:
            n_args = functions.builtin_params.get(self.func, functions.builtin_params_default)
            if len(self.args) != n_args:
                gen_error(self.get_pos(),
                          f"Invalid number of arguments to function \"{self.func}\" (expected {n_args}, got {len(self.args)})")

            return_var = Gen.temp_var()
            self._ret_var = return_var

            code = Instructions()
            args = []
            for a in self.args:
                ac, av = a.get()
                code += ac
                args.append(av)

            while len(args) < 2:
                args.append("_")

            return code + MInstruction(MInstructionType.OP, [self.func, return_var] + list(map(str, args)))

        code = Instructions()
        for i, arg in enumerate(self.args):
            valc, valv = arg.get()
            code += valc
            code += MInstruction(MInstructionType.SET, [f"__f_{self.func}_a{i}", valv])
            self._ret_var = Var(f"__f_{self.func}_retv", True)

        code += f"op add __f_{self.func}_ret @counter 1\nset @counter __f_{self.func}"

        return code

    def get(self):
        return self.generate(), self._ret_var

    def table_rename(self, variables: dict):
        return CallNode(self.pos, self.func, [a.table_rename(variables) for a in self.args])

    def function_rename(self, name: str):
        return CallNode(self.pos, self.func, [a.function_rename(name) for a in self.args])


class ExpressionNode(Node):
    OPERATORS = {
        "&&": "land",
        "||": "or"
    }

    def __init__(self, pos: Position, left: Node, right: list):
        super().__init__(pos)

        self.left = left
        self.right = right

    def get_pos(self) -> Position:
        if len(self.right) > 0:
            return self.pos + self.right[-1][1].get_pos()

        return self.pos

    def get(self):
        valc, valv = self.left.get()

        if len(self.right) > 0:
            tmpv = Gen.temp_var(valv)
            code = valc + MInstruction(MInstructionType.SET, [tmpv, valv])

            for r in self.right:
                # determine operator
                op = ExpressionNode.OPERATORS.get(r[0])
                if op is None:
                    gen_error(self.get_pos(), f"Invalid operator")

                valc, valv = r[1].get()

                tmpv2 = Gen.temp_var()
                code += valc + MInstruction(MInstructionType.OP, [op, tmpv2, tmpv, valv])
                tmpv = tmpv2

            return code, tmpv

        else:
            return valc, valv

    def table_rename(self, variables: dict):
        return ExpressionNode(self.pos, self.left.table_rename(variables),
                              [(r[0], r[1].table_rename(variables)) for r in self.right])

    def function_rename(self, name: str):
        return ExpressionNode(self.pos, self.left.function_rename(name), [(r[0], r[1].function_rename(name)) for r in self.right])


class CompExpressionNode(Node):
    OPERATORS = {
        "==": "equal",
        "<": "lessThan",
        ">": "greaterThan",
        "<=": "lessThanEq",
        ">=": "greaterThanEq",
        "!=": "notEqual",
        "===": "strictEqual"
    }

    def __init__(self, pos: Position, left: Node, right: list):
        super().__init__(pos)

        self.left = left
        self.right = right

    def get_pos(self) -> Position:
        if len(self.right) > 0:
            return self.pos + self.right[-1][1].get_pos()

        return self.pos

    def get(self):
        valc, valv = self.left.get()

        if len(self.right) > 0:
            tmpv = Gen.temp_var(valv)
            code = valc + MInstruction(MInstructionType.SET, [tmpv, valv])

            for r in self.right:
                # determine operator
                op = CompExpressionNode.OPERATORS.get(r[0])
                if op is None:
                    gen_error(self.get_pos(), f"Invalid operator")

                valc, valv = r[1].get()

                tmpv2 = Gen.temp_var()
                code += valc + MInstruction(MInstructionType.OP, [op, tmpv2, tmpv, valv])
                tmpv = tmpv2

            return code, tmpv

        else:
            return valc, valv

    def table_rename(self, variables: dict):
        return CompExpressionNode(self.pos, self.left.table_rename(variables), [(r[0], r[1].table_rename(variables)) for r in self.right])

    def function_rename(self, name: str):
        return CompExpressionNode(self.pos, self.left.function_rename(name), [(r[0], r[1].function_rename(name)) for r in self.right])


class ArithExpressionNode(Node):
    OPERATORS = {
        "+": "add",
        "-": "sub",
        "<<": "shl",
        ">>": "shr",
        "&": "and",
        "|": "or",
        "^": "xor"
    }

    def __init__(self, pos: Position, left: Node, right: list):
        super().__init__(pos)

        self.left = left
        self.right = right

    def get_pos(self) -> Position:
        if len(self.right) > 0:
            return self.pos + self.right[-1][1].get_pos()

        return self.pos

    def get(self):
        valc, valv = self.left.get()

        if len(self.right) > 0:
            tmpv = Gen.temp_var(valv)
            code = valc + MInstruction(MInstructionType.SET, [tmpv, valv])

            for r in self.right:
                # determine operator
                op = ArithExpressionNode.OPERATORS.get(r[0])
                if op is None:
                    gen_error(self.get_pos(), f"Invalid operator")

                valc, valv = r[1].get()

                tmpv2 = Gen.temp_var()
                code += valc + MInstruction(MInstructionType.OP, [op, tmpv2, tmpv, valv])
                tmpv = tmpv2

            return code, tmpv

        else:
            return valc, valv

    def table_rename(self, variables: dict):
        return ArithExpressionNode(self.pos, self.left.table_rename(variables), [(r[0], r[1].table_rename(variables)) for r in self.right])

    def function_rename(self, name: str):
        return ArithExpressionNode(self.pos, self.left.function_rename(name), [(r[0], r[1].function_rename(name)) for r in self.right])


class TermNode(Node):
    OPERATORS = {
        "*": "mul",
        "/": "div",
        "**": "pow",
        "%": "mod",
        "//": "idiv"
    }

    def __init__(self, pos: Position, left: Node, right: list):
        super().__init__(pos)

        self.left = left
        self.right = right

    def get_pos(self) -> Position:
        if len(self.right) > 0:
            return self.pos + self.right[-1][1].get_pos()

        return self.pos

    def get(self):
        valc, valv = self.left.get()

        if len(self.right) > 0:
            tmpv = Gen.temp_var(valv)
            code = valc + MInstruction(MInstructionType.SET, [tmpv, valv])

            for r in self.right:
                # determine operator
                op = TermNode.OPERATORS.get(r[0])
                if op is None:
                    gen_error(self.get_pos(), f"Invalid operator")

                valc, valv = r[1].get()

                tmpv2 = Gen.temp_var()
                code += valc + MInstruction(MInstructionType.OP, [op, tmpv2, tmpv, valv])
                tmpv = tmpv2

            return code, tmpv

        else:
            return valc, valv

    def table_rename(self, variables: dict):
        return TermNode(self.pos, self.left.table_rename(variables), [(r[0], r[1].table_rename(variables)) for r in self.right])

    def function_rename(self, name: str):
        return TermNode(self.pos, self.left.function_rename(name), [(r[0], r[1].function_rename(name)) for r in self.right])


class FactorNode(Node):
    def __init__(self, pos: Position, value: Node, flags: dict):
        super().__init__(pos)

        self.value = value
        self.flags = flags

    def get_pos(self) -> Position:
        return self.pos + self.value.get_pos()

    def get(self):
        valc, valv = self.value.get()
        tmpv = Gen.temp_var(valv)
        code = valc + MInstruction(MInstructionType.SET, [tmpv, valv])

        if not self.flags["sign"]:
            code += MInstruction(MInstructionType.OP, ["sub", tmpv, "0", tmpv])
        if self.flags["not"]:
            code += MInstruction(MInstructionType.OP, ["not", tmpv, tmpv, "0"])
        if self.flags["flip"]:
            code += MInstruction(MInstructionType.OP, ["flip", tmpv, tmpv, "_"])

        return code, tmpv

    def table_rename(self, variables: dict):
        return FactorNode(self.pos, self.value.table_rename(variables), self.flags)

    def function_rename(self, name: str):
        return FactorNode(self.pos, self.value.function_rename(name), self.flags)


class ValueNode(Node):
    def __init__(self, pos: Position, value: str, is_id: bool):
        super().__init__(pos)

        self.value = value
        self.is_id = is_id

    def get_pos(self) -> Position:
        return self.pos

    def get(self):
        if Gen.REGEXES["ATTR"].fullmatch(self.value):
            tmpv = Gen.temp_var()
            spl = self.value.split(".")
            return MInstruction(MInstructionType.SENSOR, [tmpv, spl[0], spl[1].replace(".", "@")]), tmpv

        return Instructions(), Var(self.value, False)

    def set(self):
        if Gen.REGEXES["ATTR"].fullmatch(self.value):
            tmpv = Gen.temp_var()
            spl = self.value.split(".")
            return MInstruction(MInstructionType.CONTROL, [spl[1], spl[0], tmpv, "_", "_"]), tmpv

        return Instructions(), Var(self.value, False)

    def table_rename(self, variables: dict):
        return ValueNode(self.pos, variables.get(self.value, self.value), self.is_id)

    def function_rename(self, name: str):
        if self.value.startswith("@") or not self.is_id or self.value.startswith("__f") or Gen.is_global(self.value):
            return self

        return ValueNode(self.pos, f"__f_{name}_lvar_{self.value}", self.is_id)


class IndexedValueNode(Node):
    def __init__(self, pos: Position, value: str, idx: Node):
        super().__init__(pos)

        self.value = value
        self.idx = idx

    def get_pos(self) -> Position:
        return self.pos + self.idx.get_pos()

    def get(self):
        tmpv = Gen.temp_var()
        ic, iv = self.idx.get()
        return ic + MInstruction(MInstructionType.READ, [self.value, iv]), tmpv

    def set(self):
        tmpv = Gen.temp_var()
        ic, iv = self.idx.get()
        return ic + MInstruction(MInstructionType.WRITE, [tmpv, self.value, iv]), tmpv

    def table_rename(self, variables: dict):
        return IndexedValueNode(self.pos, variables.get(self.value, self.value), self.idx.table_rename(variables))

    def function_rename(self, name: str):
        if Gen.is_global(self.value):
            return self

        return IndexedValueNode(self.pos, f"__f_{name}_lvar_{self.value}", self.idx.function_rename(name))


class IfNode(Node):
    def __init__(self, pos: Position, cond: Node, code: CodeListNode, else_code: CodeListNode):
        super().__init__(pos)

        self.cond = cond
        self.code = code
        self.else_code = else_code

    def get_pos(self) -> Position:
        return self.pos + self.cond.get_pos()

    def generate(self):
        condc, condv = self.cond.get()
        code = self.code.generate()
        else_code = self.else_code.generate()

        if else_code:
            ecl = Gen.temp_lab()
            el = Gen.temp_lab()
            return condc + MppInstructionOJump(ecl, condv, "notEqual", "true") + code + MppInstructionJump(el) + \
                MppInstructionLabel(ecl) + else_code + MppInstructionLabel(el)

        else:
            el = Gen.temp_lab()
            return condc + MppInstructionOJump(el, condv, "notEqual", "true") + code + MppInstructionLabel(el)

    def table_rename(self, variables: dict):
        return IfNode(self.pos, self.cond.table_rename(variables), self.code.table_rename(variables), self.else_code.table_rename(variables))

    def function_rename(self, name: str):
        return IfNode(self.pos, self.cond.function_rename(name), self.code.function_rename(name), self.else_code.function_rename(name))


class WhileNode(Node):
    def __init__(self, pos: Position, name: str, cond: Node, code: CodeListNode):
        super().__init__(pos)

        self.name = name
        self.cond = cond
        self.code = code

    def get_pos(self) -> Position:
        return self.pos + self.cond.get_pos()

    def generate(self):
        condc, condv = self.cond.get()
        code = self.code.generate()

        return MppInstructionLabel(f"{self.name}_s") + condc + \
            MppInstructionOJump(f"{self.name}_e", condv, "notEqual", "true") + \
            code + MppInstructionJump(f"{self.name}_s") + MppInstructionLabel(f"{self.name}_e")

    def table_rename(self, variables: dict):
        return WhileNode(self.pos, self.name, self.cond.table_rename(variables), self.code.table_rename(variables))

    def function_rename(self, name: str):
        return WhileNode(self.pos, self.name, self.cond.function_rename(name), self.code.function_rename(name))


class ForNode(Node):
    def __init__(self, pos: Position, name: str, init: Node, cond: Node, action: Node, code: CodeListNode):
        super().__init__(pos)

        self.name = name
        self.init = init
        self.cond = cond
        self.action = action
        self.code = code

    def get_pos(self) -> Position:
        return self.pos + self.action.get_pos()

    def generate(self):
        condc, condv = self.cond.get()
        init = self.init.generate()
        action = self.action.generate()
        code = self.code.generate()

        return init + MppInstructionLabel(f"{self.name}_s") + condc + \
            MppInstructionOJump(f">{self.name}_e", condv, "notEqual", "true") + \
            code + action + MppInstructionJump(f"{self.name}_s") + MppInstructionLabel(f"{self.name}_e")

    def table_rename(self, variables: dict):
        return ForNode(self.pos, self.name, self.init.table_rename(variables), self.cond.table_rename(variables), self.action.table_rename(variables),
                       self.code.table_rename(variables))

    def function_rename(self, name: str):
        return ForNode(self.pos, self.name, self.init.function_rename(name), self.cond.function_rename(name), self.action.function_rename(name),
                       self.code.function_rename(name))


class RangeNode(Node):
    def __init__(self, pos: Position, name: str, counter: str, until: Node, code: CodeListNode):
        super().__init__(pos)

        self.name = name
        self.counter = counter
        self.until = until
        self.code = code

    def get_pos(self) -> Position:
        return self.pos + self.until.pos

    def generate(self):
        untilc, untilv = self.until.get()
        code = self.code.generate()

        return MInstruction(MInstructionType.SET, [self.counter, "0"]) + MppInstructionLabel(f"{self.name}_s") + \
            untilc + MppInstructionOJump(f"{self.name}_e", self.counter, "greaterThanEq", untilv) + \
            code + MInstruction(MInstructionType.OP, ["add", self.counter, self.counter, "1"]) + \
            MppInstructionJump(f"{self.name}_s") + MppInstructionLabel(f"{self.name}_e")

    def table_rename(self, variables: dict):
        return RangeNode(self.pos, self.name, variables.get(self.counter, self.counter), self.until.table_rename(variables),
                         self.code.table_rename(variables))

    def function_rename(self, name: str):
        return RangeNode(self.pos, self.name, f"__f_{name}_lvar_{self.counter}", self.until.function_rename(name),
                         self.code.function_rename(name))


class FunctionNode(Node):
    def __init__(self, pos: Position, name: str, args: list, code: CodeListNode):
        super().__init__(pos)

        self.name = name
        self.args = args
        self.code = code

    def get_pos(self) -> Position:
        return self.pos

    def generate(self):
        args = {arg: f"__f_{self.name}_a{i}" for i, arg in enumerate(self.args)}

        Gen.push_globals()

        for node in self.code.code:
            if isinstance(node, GlobalNode):
                Gen.add_globals(node.vars)

        end_label = Gen.temp_lab()
        code = MInstruction(MInstructionType.OP, ["add", f"__f_{self.name}", "counter", "1"]) + \
            MppInstructionJump(end_label) + \
            self.code.table_rename(args).function_rename(self.name).generate() + \
            MInstruction(MInstructionType.SET, ["@counter", f"__f_{self.name}_ret"]) + \
            MppInstructionLabel(end_label)

        Gen.pop_globals()

        return code


class EndNode(Node):
    def __init__(self, pos: Position):
        super().__init__(pos)

    def get_pos(self) -> Position:
        return self.pos

    def generate(self):
        return MInstruction(MInstructionType.JUMP, ["0", "always", "_", "_"])


class GlobalNode(Node):
    def __init__(self, pos: Position, variables: list):
        super().__init__(pos)

        self.vars = variables

    def get_pos(self) -> Position:
        return self.pos
