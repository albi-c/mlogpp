import re

from .generator import Gen
from .functions import PRECALC

class Optimizer:
    """
    optimizes generated code
    """

    REGEXES = {
        # setting temporary variable
        "TMP_SET": re.compile(r"^set __tmp\d+ .+$"),\
        # reading to temporary variable
        "TMP_READ": re.compile(r"^read __tmp\d+ \S+ \S+$"),
        # operation to temporary variable
        "TMP_OP": re.compile(r"^op [a-zA-Z]+ __tmp\d+ \S+ \S+$"),
        # sensor to temporary variable
        "TMP_SENS": re.compile(r"^sensor __tmp\d+ \S+ \S+$"),

        # assigning from temporary variable
        "TA_SET": re.compile(r"^set [a-zA-Z_@][a-zA-Z_0-9]* __tmp\d+$"),

        # precalculatable operation
        "PC_OP": re.compile(r"op [a-zA-Z]+ \S+ \d+(\.\d+)? \d+(\.\d+)?")
    }

    def optimize(code: str) -> str:
        """
        optimize generated code
        """
        
        for i in range(1, 11):
            while True:
                code, _ = Optimizer._precalc_optimize(code)
                code, found = Optimizer._single_use_tmp(code, i)
                code, _ = Optimizer._precalc_optimize(code)

                if not found:
                    break
        
        for i in range(10, 0, -1):
            while True:
                code, _ = Optimizer._precalc_optimize(code)
                code, found = Optimizer._single_use_tmp(code, i)
                code, _ = Optimizer._precalc_optimize(code)

                if not found:
                    break
        
        return code

    def _single_use_tmp(code: str, forward: int = 1) -> str:
        """
        optimize single use temporary variables
        """

        uses = {}
        for i in range(0, Gen.VAR_COUNT + 1):
            # split bu whitespaces
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
            
            tmp += ln + "\n"
        
        return tmp.strip(), found
    
    def _precalc_optimize(code: str) -> str:
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
