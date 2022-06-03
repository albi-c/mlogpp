import re

from .generator import Gen

class Optimizer:
    """
    optimizes generated code
    """

    REGEXES = {
        # setting temporary variable
        "TMP_SET": re.compile(r"^set __tmp\d+ .+$"),\
        # reading to temporary variable
        "TMP_READ": re.compile(r"^read __tmp\d+ \S+ \S+$"),

        # assigning from temporary variable
        "TA_SET": re.compile(r"^set [a-zA-Z_@][a-zA-Z_0-9]* __tmp\d+$")
    }

    def optimize(code: str) -> str:
        """
        optimize generated code
        """

        for i in range(1, len(code.splitlines()) + 1):
            while True:
                code, found = Optimizer._single_use_tmp(code, i)

                if not found:
                    break
        
        return code

    def _single_use_tmp(code: str, forward: int = 1) -> str:
        """
        optimize single use temporary variables
        """

        uses = {}
        for i in range(0, Gen.VAR_COUNT + 1):
            c = len(re.findall(f"__tmp{i}\\D?", code))
            if c > 0:
                uses[f"__tmp{i}"] = c
        
        found = False
        lns = code.splitlines()
        tmp = ""
        for i, ln in enumerate(lns):
            fi = i + forward

            if Optimizer.REGEXES["TMP_SET"].fullmatch(ln):
                spl = ln.split(" ", 2)
                name = spl[1]
                val = spl[2]

                if i < len(lns) - forward:
                    if uses.get(name, 0) == 2 and name in lns[fi]:
                        lns[fi] = " ".join([val if part == name else part for part in lns[fi].split(" ")])
                        found = True
                        continue
            
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
            
            tmp += ln + "\n"
        
        return tmp.strip(), found
