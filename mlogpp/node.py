from .util import Position
from .error import gen_error
from .generator import Gen, Var
from . import functions


class Node:
    """
    base node class
    """

    def __init__(self, pos: Position):
        self.pos = pos

    def get_pos(self) -> Position:
        return self.pos

    def generate(self):
        return ""

    def get(self):
        return "", ""

    def set(self):
        return "", ""

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
        return "\n".join([ln for ln in "\n".join([node.generate() for node in self.code]).splitlines() if ln])

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
        val = self.value.get()
        return f"{val[0]}\nset __f_{self.func}_retv {val[1]}"

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
            return f">{self.name}_e"
        elif self.action == "continue":
            return f">{self.name}_s"


class AssignmentNode(Node):
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
            return f"{valc}\nset {varv} {valv}\n{varc}"

        else:
            # determine operator
            op = "add" if self.op == "+=" else "sub" if self.op == "-=" else "mul" if self.op == "*=" else "div" if self.op == "/=" else ""
            if op == "":
                gen_error(self.get_pos(), f"Invalid operator: \"{self.op}\"")

            vasc, vasv = self.var.get()
            varc, varv = self.var.set()
            valc, valv = self.value.get()
            return f"{vasc}\n{valc}\nop {op} {varv} {vasv} {valv}\n{varc}"

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

            code = ""
            args = []
            for a in self.args:
                ac, av = a.get()
                code += f"{ac}\n"
                args.append(av)

            if self.func in functions.native_ret:
                args.insert(functions.native_ret[self.func], return_var)
                self._ret_var = return_var
            else:
                self._ret_var = "_"

            code += f"{self.func} {' '.join(map(str, args))}"
            return code

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

            code = ""
            args = []
            for a in self.args:
                ac, av = a.get()
                code += f"{ac}\n"
                args.append(av)

            if return_var != "_":
                args.insert(functions.native_sub_ret[self.func], return_var)

            code += f"{spl[0]} {spl[1]} {' '.join(map(str, args))}"
            return code

        elif self.func in functions.builtin:
            n_args = functions.builtin_params.get(self.func, functions.builtin_params_default)
            if len(self.args) != n_args:
                gen_error(self.get_pos(),
                          f"Invalid number of arguments to function \"{self.func}\" (expected {n_args}, got {len(self.args)})")

            return_var = Gen.temp_var()
            self._ret_var = return_var

            code = ""
            args = []
            for a in self.args:
                ac, av = a.get()
                code += f"{ac}\n"
                args.append(av)

            while len(args) < 2:
                args.append("_")

            return f"{code}\nop {self.func} {return_var} {' '.join(map(str, args))}"

        code = ""
        for i, arg in enumerate(self.args):
            valc, valv = arg.get()
            code += f"{valc}\nset __f_{self.func}_a{i} {valv}\n"
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
            code = f"{valc}\nset {tmpv} {valv}"

            for r in self.right:
                # determine operator
                op = "land" if r[0] == "&&" else "or" if r[0] == "||" else ""
                if op == "":
                    gen_error(self.get_pos(), f"Invalid operator")

                valc, valv = r[1].get()

                tmpv2 = Gen.temp_var()
                code += f"\n{valc}\nop {op} {tmpv2} {tmpv} {valv}"
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
            code = f"{valc}\nset {tmpv} {valv}"

            for r in self.right:
                # determine operator
                op = "equal" if r[0] == "==" else "lessThan" if r[0] == "<" else "greaterThan" if r[
                                                                                                      0] == ">" else "lessThanEq" if \
                    r[0] == "<=" \
                    else "greaterThanEq" if r[0] == ">=" else "notEqual" if r[0] == "!=" else "strictEqual" if r[
                                                                                                                   0] == "===" else ""
                if op == "":
                    gen_error(self.get_pos(), f"Invalid operator")

                valc, valv = r[1].get()

                tmpv2 = Gen.temp_var()
                code += f"\n{valc}\nop {op} {tmpv2} {tmpv} {valv}"
                tmpv = tmpv2

            return code, tmpv

        else:
            return valc, valv

    def table_rename(self, variables: dict):
        return CompExpressionNode(self.pos, self.left.table_rename(variables), [(r[0], r[1].table_rename(variables)) for r in self.right])

    def function_rename(self, name: str):
        return CompExpressionNode(self.pos, self.left.function_rename(name), [(r[0], r[1].function_rename(name)) for r in self.right])


class ArithExpressionNode(Node):
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
            code = f"{valc}\nset {tmpv} {valv}"

            for r in self.right:
                # determine operator
                op = "add" if r[0] == "+" else "sub" if r[0] == "-" else ""
                if op == "":
                    gen_error(self.get_pos(), f"Invalid operator")

                valc, valv = r[1].get()

                tmpv2 = Gen.temp_var()
                code += f"\n{valc}\nop {op} {tmpv2} {tmpv} {valv}"
                tmpv = tmpv2

            return code, tmpv

        else:
            return valc, valv

    def table_rename(self, variables: dict):
        return ArithExpressionNode(self.pos, self.left.table_rename(variables), [(r[0], r[1].table_rename(variables)) for r in self.right])

    def function_rename(self, name: str):
        return ArithExpressionNode(self.pos, self.left.function_rename(name), [(r[0], r[1].function_rename(name)) for r in self.right])


class TermNode(Node):
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
            code = f"{valc}\nset {tmpv} {valv}"

            for r in self.right:
                # determine operator
                op = "mul" if r[0] == "*" else "div" if r[0] == "/" else "pow" if r[0] == "**" else ""
                if op == "":
                    gen_error(self.get_pos(), f"Invalid operator")

                valc, valv = r[1].get()

                tmpv2 = Gen.temp_var()
                code += f"\n{valc}\nop {op} {tmpv2} {tmpv} {valv}"
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
        code = f"{valc}\nset {tmpv} {valv}"

        if not self.flags["sign"]:
            code += f"\nop sub {tmpv} 0 {tmpv}"
        if self.flags["not"]:
            code += f"\nop not {tmpv} {tmpv} 0"
        if self.flags["flip"]:
            code += f"\nop flip {tmpv} {tmpv} _"

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
            return f"sensor {tmpv} {self.value.replace('.', ' @')}", tmpv

        return "", Var(self.value, False)

    def set(self):
        if Gen.REGEXES["ATTR"].fullmatch(self.value):
            tmpv = Gen.temp_var()
            spl = self.value.split(".")
            return f"control {spl[1]} {spl[0]} {tmpv} _ _", tmpv

        return "", Var(self.value, False)

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
        return f"{ic}\nread {tmpv} {self.value} {iv}", tmpv

    def set(self):
        tmpv = Gen.temp_var()
        ic, iv = self.idx.get()
        return f"{ic}\nwrite {tmpv} {self.value} {iv}", tmpv

    def table_rename(self, variables: dict):
        return IndexedValueNode(self.pos, variables.get(self.value, self.value), self.idx.table_rename(variables))

    def function_rename(self, name: str):
        if Gen.is_global(self.value):
            return self

        return IndexedValueNode(self.pos, f"__f_{name}_lvar_{self.value}", self.idx.function_rename(name))


class IfNode(Node):
    def __init__(self, pos: Position, cond: Node, code: Node, else_code: Node):
        super().__init__(pos)

        self.cond = cond
        self.code = code
        self.else_code = else_code

    def get_pos(self) -> Position:
        return self.pos + self.cond.get_pos()

    def generate(self):
        condc, condv = self.cond.get()
        code = self.code.generate().strip()
        else_code = self.else_code.generate().strip()

        if else_code:
            ecl = Gen.temp_lab()
            el = Gen.temp_lab()
            return f"{condc}\n>{ecl} {condv} notEqual true\n{code}\n>{el}\n<{ecl}\n{else_code}\n<{el}"

        else:
            el = Gen.temp_lab()
            return f"{condc}\n>{el} {condv} notEqual true\n{code}\n<{el}"

    def table_rename(self, variables: dict):
        return IfNode(self.pos, self.cond.table_rename(variables), self.code.table_rename(variables), self.else_code.table_rename(variables))

    def function_rename(self, name: str):
        return IfNode(self.pos, self.cond.function_rename(name), self.code.function_rename(name), self.else_code.function_rename(name))


class WhileNode(Node):
    def __init__(self, pos: Position, name: str, cond: Node, code: Node):
        super().__init__(pos)

        self.name = name
        self.cond = cond
        self.code = code

    def get_pos(self) -> Position:
        return self.pos + self.cond.get_pos()

    def generate(self):
        condc, condv = self.cond.get()
        code = self.code.generate().strip()

        return f"<{self.name}_s\n{condc}\n>{self.name}_e {condv} notEqual true\n{code}\n>{self.name}_s\n<{self.name}_e"

    def table_rename(self, variables: dict):
        return WhileNode(self.pos, self.name, self.cond.table_rename(variables), self.code.table_rename(variables))

    def function_rename(self, name: str):
        return WhileNode(self.pos, self.name, self.cond.function_rename(name), self.code.function_rename(name))


class ForNode(Node):
    def __init__(self, pos: Position, name: str, init: Node, cond: Node, action: Node, code: Node):
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
        code = self.code.generate().strip()

        return f"{init}\n<{self.name}_s\n{condc}\n>{self.name}_e {condv} notEqual true\n{code}\n{action}\n>{self.name}_s\n<{self.name}_e"

    def table_rename(self, variables: dict):
        return ForNode(self.pos, self.name, self.init.table_rename(variables), self.cond.table_rename(variables), self.action.table_rename(variables),
                       self.code.table_rename(variables))

    def function_rename(self, name: str):
        return ForNode(self.pos, self.name, self.init.function_rename(name), self.cond.function_rename(name), self.action.function_rename(name),
                       self.code.function_rename(name))


class FunctionNode(Node):
    name: str
    args: list
    code: CodeListNode

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
        code = f"op add __f_{self.name} @counter 1\n>{end_label}\n"
        code += self.code.table_rename(args).function_rename(self.name).generate()
        code += f"\nset @counter __f_{self.name}_ret\n<{end_label}"

        Gen.pop_globals()

        return code


class EndNode(Node):
    def __init__(self, pos: Position):
        super().__init__(pos)

    def get_pos(self) -> Position:
        return self.pos

    def generate(self):
        return "jump 0 always _ _"


class GlobalNode(Node):
    def __init__(self, pos: Position, variables: list):
        super().__init__(pos)

        self.vars = variables

    def get_pos(self) -> Position:
        return self.pos
