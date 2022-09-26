import re

from .generator import Gen
from .functions import PRECALC, JC_REPLACE


class Optimizer:
    """
    optimizes generated code
    """

    REGEXES = {
        # setting temporary variable
        "TMP_SET": re.compile(r"^set __tmp\d+ .+$"),
        # reading to temporary variable
        "TMP_READ": re.compile(r"^read __tmp\d+ \S+ \S+$"),
        # operation to temporary variable
        "TMP_OP": re.compile(r"^op [a-zA-Z]+ __tmp\d+ \S+ \S+$"),
        # sensor to temporary variable
        "TMP_SENS": re.compile(r"^sensor __tmp\d+ \S+ \S+$"),
        # getlink to temporary variable
        "TMP_GETL": re.compile(r"^getlink __tmp\d+ \S+$"),
        # radar/uradar to temporary variable
        "TMP_RAD": re.compile(r"^u?radar \S+ \S+ \S+ \S+ \S+ \S+ __tmp\d+$"),

        # jump operation to temporary variable
        "TMP_J_OP": re.compile(r"^op (equal|notEqual|greaterThan|lessThan|greaterThanEq|lessThanEq) __tmp\d+ \S+ \S+$"),
        # temporary variable to jump
        "TMP_J": re.compile(r"^\S+ __tmp\d+ notEqual true$"),

        # assigning from temporary variable
        "TA_SET": re.compile(r"^set [a-zA-Z_@][a-zA-Z_0-9]* __tmp\d+$"),

        # operation eligible to be precalculated
        "PC_OP": re.compile(r"^op [a-zA-Z]+ \S+ \d+(\.\d+)? \d+(\.\d+)?$")
    }

    @staticmethod
    def optimize(code: str) -> str:
        """
        optimize generated code
        """
        
        for i in range(1, 11):
            while True:
                code, _ = Optimizer._precalculate_optimize(code)
                code, found = Optimizer._single_use_tmp(code, i)
                code, _ = Optimizer._precalculate_optimize(code)

                if not found:
                    break
        
        for i in range(10, 0, -1):
            while True:
                code, _ = Optimizer._precalculate_optimize(code)
                code, found = Optimizer._single_use_tmp(code, i)
                code, _ = Optimizer._precalculate_optimize(code)

                if not found:
                    break
        
        return code

    @staticmethod
    def _single_use_tmp(code: str, forward: int = 1) -> tuple[str, bool]:
        """
        optimize single use temporary variables
        """

        uses = {}
        for i in range(0, Gen.VAR_COUNT + 1):
            # split by whitespaces
            s = re.split("\\s+", code)
            # count variable usage
            c = s.count(f"__tmp{i}")

            if c > 0:
                uses[f"__tmp{i}"] = c
        
        found = False
        lns = code.splitlines()
        tmp = ""
        for i, ln in enumerate(lns):
            fi = i + forward

            # setting value to temporary variable
            if Optimizer.REGEXES["TMP_SET"].fullmatch(ln):
                spl = ln.split(" ", 2)
                name = spl[1]
                val = spl[2]

                if i < len(lns) - forward:
                    if uses.get(name, 0) == 2 and name in lns[fi]:
                        lns[fi] = " ".join([val if part == name else part for part in lns[fi].split(" ")])
                        found = True
                        continue
            
            # reading from memory cell to temporary variable
            elif Optimizer.REGEXES["TMP_READ"].fullmatch(ln):
                spl = ln.split(" ", 3)
                name = spl[1]

                if i < len(lns) - forward:
                    if uses.get(name, 0) == 2 and Optimizer.REGEXES["TA_SET"].fullmatch(lns[fi]):
                        spl_ = lns[fi].split(" ", 2)
                        if name == spl_[2]:
                            lns[fi] = f"read {spl_[1]} {spl[2]} {spl[3]}"
                            found = True
                            continue
            
            # operation to temporary variable
            elif Optimizer.REGEXES["TMP_OP"].fullmatch(ln):
                spl = ln.split(" ", 4)
                name = spl[2]

                if i < len(lns) - forward:
                    if uses.get(name, 0) == 2 and Optimizer.REGEXES["TA_SET"].fullmatch(lns[fi]):
                        spl_ = lns[fi].split(" ", 2)
                        if name == spl_[2]:
                            lns[fi] = f"op {spl[1]} {spl_[1]} {spl[3]} {spl[4]}"
                            found = True
                            continue
            
            # sensor to temporary variable
            elif Optimizer.REGEXES["TMP_SENS"].fullmatch(ln):
                spl = ln.split(" ", 3)
                name = spl[1]

                if i < len(lns) - forward:
                    if uses.get(name, 0) == 2 and Optimizer.REGEXES["TA_SET"].fullmatch(lns[fi]):
                        spl_ = lns[fi].split(" ", 2)
                        if name == spl_[2]:
                            lns[fi] = f"sensor {spl_[1]} {spl[2]} {spl[3]}"
                            found = True
                            continue
            
            # getlink to temporary variable
            elif Optimizer.REGEXES["TMP_GETL"].fullmatch(ln):
                spl = ln.split(" ", 2)
                name = spl[1]

                if i < len(lns) - forward:
                    if uses.get(name, 0) == 2 and Optimizer.REGEXES["TA_SET"].fullmatch(lns[fi]):
                        spl_ = lns[fi].split(" ", 2)
                        if name == spl_[2]:
                            lns[fi] = f"getlink {spl_[1]} {spl[2]}"
                            found = True
                            continue
            
            # radar to temporary variable
            elif Optimizer.REGEXES["TMP_RAD"].fullmatch(ln):
                spl = ln.split(" ", 7)
                name = spl[7]

                if i < len(lns) - forward:
                    if uses.get(name, 0) == 2 and Optimizer.REGEXES["TA_SET"].fullmatch(lns[fi]):
                        spl_ = lns[fi].split(" ", 2)
                        if name == spl_[2]:
                            lns[fi] = f"{' '.join(spl[:-1])} {spl_[1]}"
                            found = True
                            continue
            
            # temporary variable to jump
            if Optimizer.REGEXES["TMP_J_OP"].fullmatch(ln):
                spl = ln.split(" ", 4)
                name = spl[2]

                if i < len(lns) - forward and spl[1] in JC_REPLACE:
                    if uses.get(name, 0) == 2 and Optimizer.REGEXES["TMP_J"].fullmatch(lns[fi]):
                        spl_ = lns[fi].split(" ", 3)
                        if name == spl_[1]:
                            lns[fi] = f"{spl_[0]} {spl[3]} {JC_REPLACE[spl[1]]} {spl[4]}"
                            found = True
                            continue
            
            tmp += ln + "\n"
        
        return tmp.strip(), found

    @staticmethod
    def _precalculate_optimize(code: str) -> tuple[str, bool]:
        """
        precalculate values where possible
        """

        lns = code.splitlines()
        tmp = ""
        found = False
        for ln in lns:
            if Optimizer.REGEXES["PC_OP"].fullmatch(ln):
                spl = ln.split(" ", 4)

                op = spl[1]
                name = spl[2]

                a = float(spl[3])
                b = float(spl[4])
                if a.is_integer():
                    a = int(a)
                if b.is_integer():
                    b = int(b)

                if op in PRECALC:
                    try:
                        result = PRECALC[op](a, b)
                    except TypeError:
                        pass
                    else:
                        ln = f"set {name} {result}"
                        found = True

            tmp += ln + "\n"
        
        return tmp.strip(), found
