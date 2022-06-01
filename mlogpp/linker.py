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

        offset = 0
        tmp = []
        for code in codes:
            # relocate jumps
            c, o = Linker._relocate(code, offset)

            tmp.append(c)
            offset += o

        return "\n".join(tmp)
    
    @staticmethod
    def _relocate(code: str, offset: int) -> str:
        """
        relocate jumps in compiled code
        """

        tmp = ""
        nl = 0
        for ln in code.strip().splitlines():
            # check if line is a jump
            if ln.startswith("jump "):
                spl = ln.split(" ")

                # check if jump has enough arguments
                if len(spl) != 5:
                    link_error(Position(nl, 0, ln, len(ln)), "Invalid jump instruction")

                # check if jump address is valid
                pos = spl[1]
                try:
                    pos = int(pos)
                except ValueError:
                    link_error(Position(nl, len(spl[0]) + 1, ln, len(spl[1])), "Invalid jump address")
                
                ln = f"jump {pos + offset} {spl[2]} {spl[3]} {spl[4]}"

            nl += 1
            tmp += ln + "\n"
        
        return tmp.strip(), nl
