import re


class Preprocessor:
    """
    Resolves constants.
    """

    # code regexes
    REGEXES = {
        "CONST": re.compile(r"^const [a-zA-Z_][a-zA-Z_0-9]* = .+$")
    }

    @staticmethod
    def preprocess(code: str) -> str:
        """
        Resolve constants in code.

        Args:
            code: The code to be processed.

        Returns:
            The code with resolved constants.
        """

        consts = {}
        tmp = ""
        for ln in code.splitlines():
            # check if line defines a constant
            if Preprocessor.REGEXES["CONST"].fullmatch(ln):
                spl = ln.split(" = ", 1)
                consts[spl[0].split(" ")[1]] = spl[1]

                tmp += "\n"

                continue
            
            # replace constant references with values sorted by length in order to not replace non-equal constants
            for k, v in sorted(consts.items(), key=lambda pair: len(pair[0]), reverse=True):
                ln = ln.replace(k, v)
            
            tmp += ln + "\n"
        
        return tmp
