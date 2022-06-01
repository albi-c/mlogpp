import re

from .generator import Gen

class Optimizer:
    """
    optimizes generated code
    """

    REGEXES = {
        # setting temporary variable
        "SU_SET": re.compile(r"^set __tmp\d+ .+$")
    }

    def optimize(code: str) -> str:
        """
        optimize generated code
        """

        while True:
            code, changed = Optimizer._single_use_tmp(code)

            if not changed:
                break
        
        return code

    def _single_use_tmp(code: str) -> str:
        """
        optimize single use temporary variables
        """

        uses = {}
        for i in range(1, Gen.VAR_COUNT + 1):
            c = len(re.findall(f"__tmp{i}\\D", code))
            if c > 0:
                uses[f"__tmp{i}"] = c
        
        changed = False
        values = {}
        tmp = ""
        for i, ln in enumerate(code.splitlines()):
            if Optimizer.REGEXES["SU_SET"].fullmatch(ln):
                spl = ln.split(" ", 2)
                if uses.get(spl[1], -1) == 2:
                    values[spl[1]] = spl[2]
                    changed = True
                    continue
            
            tmp += " ".join([values.get(part, part) for part in ln.split(" ")]) + "\n"
        
        return tmp.strip(), changed
