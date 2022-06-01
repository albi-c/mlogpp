from .lexer import Position
from .error import link_error

class Linker:
    """
    links generated code together
    """

    @staticmethod
    def link(codes: list) -> str:
        """
        links generated code together
        """

        # find labels
        code = "\n".join([ln for ln in "\n".join(codes).splitlines() if ln])
        labels = {}
        labelc = 0
        tmp = ""
        for i, ln in enumerate(code.splitlines()):
            # is a label
            if ln.startswith("<"):
                labels[ln[1:]] = i - labelc
                labelc += 1
                continue

            tmp += ln + "\n"
        
        # resolve jumps
        code = ""
        for i, ln in enumerate(tmp.splitlines()):
            # is a jump
            if ln.startswith(">"):
                # jump data
                jd = ln[1:].split(" ", 1)

                if len(jd) == 1:
                    # always jump
                    code += f"jump {labels[jd[0]]} always _ _\n"

                elif len(jd) == 2:
                    # conditional jump
                    if jd[1].startswith("!"):
                        code += f"jump {labels[jd[0]]} notEqual {jd[1][1:]} true\n"
                    else:
                        code += f"jump {labels[jd[0]]} notEqual {jd[1][1:]} false\n"
                
                continue
            
            code += ln + "\n"
        
        return code.strip()
