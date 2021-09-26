from .lexer import Position
from .error import link_error

class Linker:
    def link(codes: list) -> str:
        offset = 0
        tmp = []
        for code in codes:
            c, o = Linker._relocate(code, offset)

            tmp.append(c)
            offset += o

        return "\n".join(tmp)
    
    def _relocate(code: str, offset: int) -> str:
        tmp = ""
        nl = 0
        for ln in code.strip().splitlines():
            if ln.startswith("jump "):
                spl = ln.split(" ")

                if len(spl) != 5:
                    link_error(Position(nl, 0, ln, len(ln)), "Invalid jump instruction")

                pos = spl[1]
                try:
                    pos = int(pos)
                except ValueError:
                    link_error(Position(nl, len(spl[0]) + 1, ln, len(spl[1])), "Invalid jump address")
                
                ln = f"jump {pos + offset} {spl[2]} {spl[3]} {spl[4]}"

            nl += 1
            tmp += ln + "\n"
        
        return tmp.strip(), nl
