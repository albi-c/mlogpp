import re, math

from .parser_ import *
from .gerror import gen_error, gen_undefined_error
from . import functions, gerror

GEN_REGEXES = {
    "LABEL": re.compile(r"^<[a-zA-Z_@][a-zA-Z_0-9]*$"),
    "JUMP":  re.compile(r"^>[a-zA-Z_@][a-zA-Z_0-9]*$"),
    "CJMP":  re.compile(r"^>[a-zA-Z_@][a-zA-Z_0-9]* \!?[a-zA-Z_0-9@]+$"),
    "EJMP":  re.compile(r"^>[a-zA-Z_@][a-zA-Z_0-9]* [a-zA-Z_0-9@\.]+ ((==)|(\!=)|(>=)|(<=)|>|<) [a-zA-Z_0-9@\.]+$"),

    "TMPS":  re.compile(r"^set __tmp[0-9]+ .+$"),
    "TMPSE": re.compile(r"^sensor __tmp[0-9]+ \S+ \S+$"),
    "TMPSA": re.compile(r"^set [a-zA-Z_@][a-zA-Z_0-9]* __tmp[0-9]+$"),

    "TMPOP": re.compile(r"^op [a-zA-Z]+( [a-zA-Z_@][a-zA-Z_0-9]*){2} .+$"),

    "MJUMP": re.compile(r"^jump [0-9]+ [a-zA-Z]+ [a-zA-Z_0-9@]+ [a-zA-Z_0-9@]+$"),

    "MCALC": re.compile(r"^op [a-zA-Z]+ [a-zA-Z_0-9@]+ [0-9]+(\.[0-9]+)? [0-9]+(\.[0-9]+)?$"),

    "VARA":  re.compile(r"^(set \S+ \S+)|(op [a-zA-Z]+( \S+){3})$"),

    "NUM":   re.compile(r"^[0-9]+(\.[0-9]+)?$"),

    "IATTR": re.compile(r"^[a-zA-Z_@][a-zA-Z_0-9]*\.[a-zA-Z_@][a-zA-Z_0-9]*$"),

    "TCOMP": re.compile(r"^op ((equal)|(notEqual)|(greaterThan)|(lessThan)|(greaterThanEq)|(lessThanEq)) __tmp[0-9]+ \S+ \S+$"),
    "TJUMP": re.compile(r"^>__mpp[0-9]+ !__tmp[0-9]+$"),

    "VARU":  re.compile(r"^[a-zA-Z_][a-zA-Z_0-9]*$")
}

PRECALC = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b,
    "idiv": lambda a, b: a // b,
    "mod": lambda a, b: a % b,
    "pow": lambda a, b: a ** b,
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
    "sqrt": lambda a, _: math.sqrt(a)

    # not implemented: angle, length, noise, rand, sin, cos, tan, asin, acos, atan
    # equal and notEqual are not implemented because they use type conversion
}

NATIVE_RETURN_POS = {
    "set": 0,
    "op": 1,
    "read": 0,
    "getlink": 0,
    "sensor": 0,
    "lookup": 1
}

NATIVE_CONST_INPUTS = {
    "draw": [0],
    "control": [0],
    "sensor": [1],
    "op": [0],
    "jump": [1],
    "radar": [0, 1, 2, 3],
    "ucontrol": [0],
    "uradar": [0, 1, 2, 3],
    "ulocate": [0, 1]
}

PARAM_NO_TMP = {
    "set": [0],
    "op": [1],
    "lookup": [0, 1],
    "read": [0],
    "drawflush": [0],
    "printflush": [0],
    "getlink": [0],
    "radar": [6],
    "sensor": [0],
    "uradar": [6],
    "ubind": [0],
    "ulocate": [4, 5, 6, 7]
}

JUMP_CONDITIONS_REPLACE = {
    "equal": "!=",
    "notEqual": "==",
    "greaterThan": "<=",
    "lessThan": ">=",
    "greaterThanEq": "<",
    "lessThanEq": ">"
}

JUMP_CONDITION = {
    "==": "equal",
    "!=": "notEqual",
    ">": "greaterThan",
    "<": "lessThan",
    ">=": "greaterThanEq",
    "<=": "lessThanEq"
}

class Generator:
    def generate(self, node: AST, optimize_options: dict = None) -> str:
        self.tmpv = 0
        self.tmpl = 0
        self.func_stack = []
        self.loop_stack = []
        self.no_generate_tmp = False
        self.var_list = set(self._generate_var_list(node))

        funcs = []
        for v in self.var_list:
            if ":" in v:
                spl = v.split(":", 1)
                if spl[0] in funcs:
                    gen_error(None, f"Redefinition of function \"{spl[0]}\"")
                funcs.append(spl[0])

        print(self.var_list)

        code = self._code_node_join(node)

        return self.postprocess(self.optimize(code, optimize_options))
    
    def _code_join(self, codel: list, to_pos: int = None) -> str:
        code = ""
        for c in codel[:(to_pos + 1 if to_pos is not None else len(codel))]:
            r = self._generate(c)
            code += (r if type(r) == str else r[0]) + "\n"
        
        return "\n".join([l for l in code.strip().splitlines() if l.strip()])
    
    def _code_node_join(self, node: Node, to_pos: int = None) -> str:
        return self._code_join(node.code, to_pos)
    
    def optimize(self, code: str, optimize_options: dict = None) -> str:
        options = {
            "enable": True,
            "unused": True
        }

        if optimize_options is not None:
            for k, v in optimize_options.items():
                options[k] = v
        
        if not options["enable"]:
            return code

        tmp = code

        for _ in range(10):
            for _ in range(1, 101):
                tmp, found = self._single_tmp_optimize(tmp, 1)
                if not found:
                    break
            
            for i in range(1, 11):
                tmp, found = self._single_tmp_optimize(tmp, i)
            
            for _ in range(1, 11):
                tmp, found = self._negative_optimize(tmp)

        for i in range(1, 101):
            tmp, found = self._forward_use_optimize(tmp, i)
            if not found:
                break
        
        for _ in range(10):
            tmp, found = self._precalc_optimize(tmp)

            for i in range(1, 11):
                tmp, found = self._single_tmp_optimize(tmp, i)
            
            for i in range(1, 101):
                tmp, found = self._forward_use_optimize(tmp, i)
                if not found:
                    break
        
        if options["unused"]:
            for _ in range(1, 101):
                tmp, found = self._unused_optimize(tmp)
                if not found:
                    break

        return tmp
    
    def _single_tmp_optimize(self, code: str, n_lines: int) -> str:
        uses = {}

        for i in range(1, self.tmpv + 1):
            c = len(re.findall(f"__tmp{i}\\D", code))

            if c > 0:
                uses[f"__tmp{i}"] = c
        
        found = False
        lns = code.splitlines()
        tmp = ""
        for i, ln in enumerate(lns):
            if GEN_REGEXES["TMPS"].fullmatch(ln):
                spl = ln.split(" ", 2)
                name = spl[1]
                val = spl[2]

                if i < len(lns) - n_lines:
                    if uses[name] == 2 and name in lns[i + n_lines]:
                            lns[i + n_lines] = lns[i + n_lines].replace(name, val)
                            found = True
                            continue

            elif GEN_REGEXES["TMPSE"].fullmatch(ln):
                spl = ln.split(" ", 3)
                name = spl[1]

                if i < len(lns) - n_lines:
                    if uses[name] == 2 and GEN_REGEXES["TMPSA"].fullmatch(lns[i + n_lines]):
                        spl_ = lns[i + n_lines].split(" ", 2)
                        if name == spl_[2]:
                            lns[i + n_lines] = f"sensor {spl_[1]} {spl[2]} {spl[3]}"
                            found = True
                            continue
            
            elif GEN_REGEXES["TCOMP"].fullmatch(ln):
                spl = ln.split(" ", 4)
                cond = spl[1]
                op1 = spl[3]
                op2 = spl[4]

                if i < len(lns) - n_lines:
                    if uses[name] == 2 and GEN_REGEXES["TJUMP"].fullmatch(lns[i + n_lines]):
                        spl_ = lns[i + n_lines].split(" ", 1)
                        if spl_[1][1:] == spl[2] and cond in JUMP_CONDITIONS_REPLACE:
                            lns[i + n_lines] = f"{spl_[0]} {op1} {JUMP_CONDITIONS_REPLACE[cond]} {op2}"
                            continue
                
            tmp += ln + "\n"
        
        return tmp, found
    
    def _forward_use_optimize(self, code: str, n_lines: int) -> str:
        lns = code.splitlines()
        tmp = ""
        found = False
        for i, ln in enumerate(lns):
            if GEN_REGEXES["TMPS"].fullmatch(ln):
                spl = ln.split(" ", 2)
                name = spl[1]
                val = spl[2]

                if i < len(lns) - n_lines:
                    if GEN_REGEXES["TMPOP"].fullmatch(lns[i + n_lines]):
                        spl2 = lns[i + n_lines].split(" ", 4)
                        if spl2[2] == name:
                            lns[i + n_lines] = f"{spl2[0]} {spl2[1]} {spl2[2]} {val} {spl2[4]}"
                            found = True
                            continue
            tmp += ln + "\n"
        
        return tmp, found
    
    def _precalc_optimize(self, code: str) -> str:
        lns = code.splitlines()
        tmp = ""
        found = False
        for ln in lns:
            if GEN_REGEXES["MCALC"].fullmatch(ln):
                spl = ln.split(" ", 4)
                op = spl[1]
                name = spl[2]
                n1 = float(spl[3])
                n2 = float(spl[4])

                if op in PRECALC:
                    result = PRECALC[op](n1, n2)
                    if result == int(result):
                        result = int(result)
                    
                    ln = f"set {name} {result}"
                    found = True

            tmp += ln + "\n"

        return tmp, found
    
    def _unused_optimize(self, code: str) -> str:
        tmp = ""
        found = False
        for ln in code.splitlines():
            if GEN_REGEXES["VARA"].fullmatch(ln):
                name = ""

                if ln.startswith("set"):
                    name = ln.split(" ", 2)[1]
                elif ln.startswith("op"):
                    name = ln.split(" ", 4)[2]
                
                uses = len(re.findall(name, code))

                if uses <= 1:
                    continue

            tmp += ln + "\n"

        return tmp, found
    
    def _negative_optimize(self, code: str) -> str:
        lns = code.splitlines()
        tmp = ""
        found = False
        for i, ln in enumerate(lns):
            if GEN_REGEXES["TMPS"].fullmatch(ln):
                if i < len(lns) - 1:
                    spl = ln.split(" ", 2)
                    name = spl[1]
                    val = spl[2]

                    if lns[i + 1] == f"op sub {name} 0 {name}":
                        if GEN_REGEXES["NUM"].fullmatch(val):
                            lns[i + 1] = f"set {name} -{val}"
                            continue

            tmp += ln + "\n"
        
        return tmp, found
    
    def postprocess(self, code: str) -> str:
        if not code.strip():
            return code

        tmp = ""
        labels = {}
        lc = 0

        for i, ln in enumerate(code.splitlines()):
            if ln.startswith("."):
                ln = ln[1:]
            
            if GEN_REGEXES["LABEL"].fullmatch(ln):
                labels[ln[1:]] = i - lc
                lc += 1
                continue

            if GEN_REGEXES["VARA"]:
                spl = ln.split()
                if spl and spl[0] == "set":
                    if spl[1] == spl[2]:
                        continue
                
            
            tmp += ln + "\n"
        
        tmp2 = ""
        for i, ln in enumerate(tmp.splitlines()):
            name = ""
            cond = False
            cvar = "_"
            invert = False

            if GEN_REGEXES["JUMP"].fullmatch(ln):
                name = ln[1:]
            elif GEN_REGEXES["CJMP"].fullmatch(ln):
                spl = ln.split()
                name = spl[0][1:]
                cond = True
                invert = spl[1].startswith("!")
                cvar = spl[1][1:] if invert else spl[1]
            elif GEN_REGEXES["EJMP"].fullmatch(ln):
                spl = ln.split()
                name = spl[0][1:]
                op1 = spl[1]
                cond = spl[2]

                if not cond in JUMP_CONDITION:
                    gen_error(None, f"Unknown jump condition \"{cond}\"")
                cond = JUMP_CONDITION[cond]

                op2 = spl[3]
                if name in labels:
                    tmp2 += f"jump {labels[name]} {cond} {op1} {op2}\n"
                else:
                    gen_error(None, f"Unknown label \"{name}\"")
                continue
            
            if name == "":
                tmp2 += ln + "\n"
            else:
                if name in labels:
                    tmp2 += f"jump {labels[name]} {'always' if not cond else 'notEqual' if invert else 'equal'} {cvar} true\n"
                else:
                    gen_error(None, f"Unknown label \"{name}\"")
        
        tmp = ""
        lnc = len(tmp2.strip().splitlines())
        for i, ln in enumerate(tmp2.splitlines()):
            if GEN_REGEXES["MJUMP"].fullmatch(ln):
                spl = ln.split(" ", 4)
                if int(spl[1]) >= lnc:
                    ln = f"{spl[0]} 0 {spl[2]} {spl[3]} {spl[4]}"

            tmp += ln + "\n"
        
        if tmp.splitlines()[-1].startswith("jump 0"):
            tmp = "\n".join(tmp.splitlines()[:-1])
        
        return tmp.strip()
    
    def _generate(self, node: Node):
        t = type(node)

        if t == Node:
            gen_error(node, "Invalid node")
        elif t == CodeNode:
            return "\n".join([str(self._generate(c)) for c in node.code])
        elif t == ValueNode:
            if self.no_generate_tmp:
                var = str(node.value)
            else:
                var = self.get_tmp_var()

            if GEN_REGEXES["IATTR"].fullmatch(node.value):
                spl = node.value.split(".")

                if spl[0] not in self.var_list:
                    gen_undefined_error(node, spl[0])
                
                return f"sensor {var} {spl[0]} @{spl[1]}", var
            
            if type(node.value) == str and not (node.value.startswith("\"") and node.value.endswith("\"")):
                if GEN_REGEXES["VARU"].fullmatch(node.value) and node.value not in self.var_list:
                    gen_undefined_error(node, node.value)

            return f"set {var} {node.value}" if not self.no_generate_tmp else "", var
        elif t == AtomNode:
            return self._generate(node.value)
        elif t == AssignmentNode:
            if node.atype == "=":
                tmp, var = self._generate(node.right)

                if GEN_REGEXES["IATTR"].fullmatch(node.left):
                    spl = node.left.split(".", 1)
                    return f"{tmp}\ncontrol {spl[1]} {spl[0]} {var} _ _ _"

                return f"{tmp}\nset {node.left} {var}"
            elif node.atype in ["+=", "-=", "*=", "/="]:
                at = node.atype
                op = "add" if at == "+=" else "sub" if at == "-=" else "mul" if at == "*=" else "div" if at == "/=" else ""
                if op == "":
                    gen_error(node, f"Invalid operator: \"{at}\"")
                
                tmp, var = self._generate(node.right)
                return f"{tmp}\nop {op} {node.left} {node.left} {var}"
        elif t == ExpressionNode:
            tmp, var = self._generate(node.left)

            if node.right is not None:
                for r in node.right:
                    op = "land" if r[0] == "&&" else "or" if r[0] == "||" else ""
                    if op == "":
                        gen_error(node, f"Invalid operator: \"{r[0]}\"")
                    
                    tmp2, var2 = self._generate(r[1])
                    tmp += f"\n{tmp2}\nop {op} {var} {var} {var2}"

            return tmp, var
        elif t == CompExpressionNode:
            tmp, var = self._generate(node.left)

            if node.right is not None:
                for r in node.right:
                    op = "equal" if r[0] == "==" else "lessThan" if r[0] == "<" else "greaterThan" if r[0] == ">" else "lessThanEq" if r[0] == "<=" \
                        else "greaterThanEq" if r[0] == ">=" else "notEqual" if r[0] == "!=" else "strictEqual" if r[0] == "===" else ""
                    if op == "":
                        gen_error(node, f"Invalid operator: \"{r[0]}\"")
                    
                    tmp2, var2 = self._generate(r[1])
                    tmp += f"\n{tmp2}\nop {op} {var} {var} {var2}"

            return tmp, var
        elif t == ArithExpNode:
            tmp, var = self._generate(node.left)

            if node.right is not None:
                for r in node.right:
                    op = "add" if r[0] == "+" else "sub" if r[0] == "-" else ""
                    if op == "":
                        gen_error(node, f"Invalid operator: \"{r[0]}\"")
                    
                    tmp2, var2 = self._generate(r[1])
                    tmp += f"\n{tmp2}\nop {op} {var} {var} {var2}"

            return tmp, var
        elif t == TermNode:
            tmp, var = self._generate(node.left)

            if node.right is not None:
                for r in node.right:
                    op = "mul" if r[0] == "*" else "div" if r[0] == "/" else "pow" if r[0] == "**" else ""
                    if op == "":
                        gen_error(node, f"Invalid operator: \"{r[0]}\"")
                    
                    tmp2, var2 = self._generate(r[1])
                    tmp += f"\n{tmp2}\nop {op} {var} {var} {var2}"

            return tmp, var
        elif t == FactorNode:
            tmp, var = self._generate(node.left)

            if not node.sign:
                tmp += f"\nop sub {var} 0 {var}"
            if node.not_:
                tmp += f"\nop not {var} {var} _"
            
            return tmp, var
        elif t == CallNode:
            if node.is_call:
                if type(node.function) == AtomNode:
                    node.function = str(node.function.value.value)
                
                if type(node.function) != str:
                        node.function = self._generate(node.function)[0].split()[-1]

                is_native = node.function in functions.native
                is_builtin = node.function in functions.builtin

                if not is_native and not is_builtin:
                    signature = functions.gen_signature(node.function, node.params)
                    found = False

                    for v in self.var_list:
                        if v == signature:
                            found = True
                            break

                        if ":" in v:
                            spl = v.split(":")
                            if spl[0] == node.function:
                                gen_error(node, f"Incorrect number of parameters to function (expected {spl[1]}, got {len(node.params)})")
                    
                    if not found:
                        gen_error(node, f"Undefined function \"{node.function}\"")

                print(node.function, is_native, is_builtin)

                tmp = ""
                params = []
                for i, arg in enumerate(node.params):
                    pnt = PARAM_NO_TMP.get(node.function, [])
                    
                    if i in pnt:
                        onogen = self.no_generate_tmp
                        self.no_generate_tmp = True
                    
                    nci = NATIVE_CONST_INPUTS.get(node.function, [])

                    if i in nci:
                        gerror.push_undefined(False)
                    
                    tmp2, var = self._generate(arg)
                    params.append(var)

                    if i in pnt:
                        self.no_generate_tmp = onogen
                    
                    if i in nci:
                        gerror.pop_undefined()

                    if is_native or is_builtin:
                        tmp += f"{tmp2}\n"
                    else:
                        tmp += f"{tmp2}\nset __f_{node.function}_arg_{i} {var}\n"
                
                if is_native:
                    req = functions.native_params[node.function]
                    while len(params) < req:
                        params.append("_")
                    
                    retpos = NATIVE_RETURN_POS.get(node.function, -1)
                    retvar = "null"
                    if retpos != -1:
                        retvar = params[retpos]
                    
                    return f"{tmp}{node.function} {' '.join(params)}", retvar
                elif is_builtin:
                    nparams = functions.builtin_params.get(node.function, functions.builtin_params_default)
                    if nparams != len(params):
                        gen_error(node, f"Incorrect number of parameters to function (expected {nparams}, got {len(params)})")

                    return f"{tmp}op {node.function} __f_{node.function}_retv {params[0] if nparams >= 1 else '_'} {params[1] if nparams >= 2 else '_'}", f"__f_{node.function}_retv"
                else:
                    return f"{tmp}op add __f_{node.function}_ret @counter 1\nset @counter __f_{node.function}", f"__f_{node.function}_retv"
            else:
                tmp, var = self._generate(node.function)

                return tmp, var
        elif t == IfNode:
            tmp2, var = self._generate(node.condition)

            if not node.elsecode:
                l_e = self.get_tmp_label()

                tmp = f"{tmp2}\n>{l_e} !{var}\n"
                tmp += self._code_node_join(node)
                tmp += f"\n<{l_e}"
            else:
                l_s = self.get_tmp_label()
                l_e = self.get_tmp_label()

                tmp = f"{tmp2}\n>{l_s} !{var}\n"
                tmp += self._code_node_join(node)
                tmp += f"\n>{l_e}\n<{l_s}\n"
                tmp += self._code_join(node.elsecode)
                tmp += f"\n<{l_e}"

            return tmp
        elif t == WhileNode:
            tmp2, var = self._generate(node.condition)

            l_v = self.get_tmp_label()
            l_e = self.get_tmp_label()

            self.loop_stack.append((l_v, l_e))

            tmp = f"<{l_v}\n{tmp2}\n>{l_e} !{var}\n"
            tmp += self._code_node_join(node)
            tmp += f"\n>{l_v}\n<{l_e}"

            self.loop_stack.pop()

            return tmp
        elif t == ForNode:
            itmp = self._generate(node.init)
            ctmp, cvar = self._generate(node.condition)
            atmp = self._generate(node.action)

            if type(itmp) != str:
                itmp = itmp[0]
            
            if type(atmp) != str:
                atmp = atmp[0]

            l_v = self.get_tmp_label()
            l_e = self.get_tmp_label()

            self.loop_stack.append((l_v, l_e))

            tmp = f"{itmp}\n<{l_v}\n{ctmp}\n>{l_e} !{cvar}\n"
            tmp += self._code_node_join(node)
            tmp += f"\n{atmp}\n>{l_v}\n<{l_e}"

            self.loop_stack.pop()

            return tmp
        elif t == FunctionNode:
            l_e = self.get_tmp_label()

            args = {a: f"__f_{node.name}_arg_{i}" for i, a in enumerate(node.args)}

            self.func_stack.append(node.name)

            to_pos = None
            for i, n in enumerate(node.code):
                if type(n) == ReturnNode:
                    to_pos = i
                    break

            tmp = f"op add __f_{node.name} @counter 1\n>{l_e}\n"
            tmp += self._code_node_join(node.rrename(args), to_pos)

            if to_pos is None:
                tmp += f"\nset @counter __f_{node.name}_ret"
            
            tmp += f"\n<{l_e}"

            self.func_stack.pop()

            return tmp
        elif t == RepeatNode:
            if node.amount == 0:
                return ""

            l_v = self.get_tmp_label()
            l_e = self.get_tmp_label()
            i = self.get_tmp_var()
            gen = self._code_node_join(node)

            tmp = f"op add {i} 0 1\n<{l_v}\nop add {i} {i} 1\n"
            tmp += gen
            tmp += f"\n>{l_e} {i} == {node.amount}\n>{l_v}\n<{l_e}"

            if len(self.optimize(tmp).strip().splitlines()) - 2 >= node.amount * len(self.optimize(gen).strip().splitlines()):
                tmp = gen
                for _ in range(node.amount - 1):
                    tmp += "\n" + gen

            return tmp
        elif t == NativeNode:
            return f".{node.code}"
        elif t == ReturnNode:
            if len(self.func_stack) < 1:
                gen_error(node, "Cannot return when not in a function")
            
            fname = self.func_stack[-1]
            rvar = f"__f_{fname}_retv"
            if node.value == None:
                return f"set {rvar} null", rvar
            else:
                tmp, var = self._generate(node.value)
                return f"{tmp}\nset {rvar} {var}\nset @counter __f_{fname}_ret", rvar
        elif t == LoopActionNode:
            if len(self.loop_stack) < 1:
                gen_error(node, "Cannot break or continue when not in a loop")
            
            loop = self.loop_stack[-1]

            if node.action == "break":
                return f">{loop[1]}"
            elif node.action == "continue":
                return f">{loop[0]}"
            
            raise RuntimeError(f"Invalid AST")
        elif t == ExternNode:
            return ""
        
        gen_error(node, "Unknown node")
    
    def _var_list_join(self, lists: list) -> list:
        tmp = []
        for l in lists:
            tmp += l
        return tmp
    
    def _generate_var_list(self, node: Node) -> list:
        t = type(node)
        
        if t in [AST, CodeNode]:
            return self._var_list_join([self._generate_var_list(n) for n in node.code])
        elif t == ValueNode:
            return [node.value] if type(node.value) == str and not (node.value.startswith("\"") and node.value.endswith("\"")) else []
        elif t == AtomNode:
            return self._generate_var_list(node.value)
        elif t == AssignmentNode:
            return [node.left] if node.atype == "=" else [] + self._generate_var_list(node.right)
        elif t in [ExpressionNode, CompExpressionNode, ArithExpNode, TermNode]:
            tmp = []
            tmp += self._generate_var_list(node.left)
            if node.right is not None:
                for _, e in node.right:
                    tmp += self._generate_var_list(e)
            return tmp
        elif t == FactorNode:
            return self._generate_var_list(node.left)
        elif t == CallNode:
            if node.is_call:
                tmp = []
                for i in PARAM_NO_TMP.get(node.function, []):
                    if i < len(node.params):
                        vl = self._generate_var_list(node.params[i])
                        tmp += vl
                return [f"__f_{node.function}_retv"] + tmp
            else:
                return self._generate_var_list(node.function)
        elif t in [IfNode, WhileNode, ForNode, RepeatNode, FunctionNode]:
            tmp = self._var_list_join([self._generate_var_list(n) for n in node.code])
            if t in [IfNode, WhileNode, ForNode]:
                tmp += self._generate_var_list(node.condition)
            if t == IfNode and node.elsecode is not None:
                tmp += self._var_list_join([self._generate_var_list(n) for n in node.elsecode])
            if t == ForNode:
                tmp += self._generate_var_list(node.init)
                tmp += self._generate_var_list(node.action)
            if t == FunctionNode:
                tmp += [f"__f_{node.name}_arg_{i}" for i, _ in enumerate(node.args)]
                tmp += [functions.gen_signature(node.name, node.args)]
            return tmp
        elif t == NativeNode:
            return []
        elif t == ReturnNode:
            return self._generate_var_list(node.value)
        elif t == LoopActionNode:
            return []
        elif t == ExternNode:
            return [node.name]

        gen_error(node, "Unknown node")

    def get_tmp_var(self) -> str:
        self.tmpv += 1
        return f"__tmp{self.tmpv}"
    
    def get_tmp_label(self) -> str:
        self.tmpl += 1
        return f"__mpp{self.tmpl}"
