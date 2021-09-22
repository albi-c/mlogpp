class Linker:
    def link(self, codes: list) -> str:
        offset = 0
        tmp = []
        for code in codes:
            c, o = self._relocate(code, offset)

            tmp.append(c)
            offset += o

        return "\n".join(tmp)
    
    def _relocate(self, code: str, offset: int) -> str:
        tmp = ""
        nl = 0
        for ln in code.strip().splitlines():
            if ln.startswith("jump "):
                spl = ln.split(" ", 2)

                if len(spl) != 3:
                    raise ValueError("Invalid linker input")

                pos = spl[1]
                try:
                    pos = int(pos)
                except ValueError:
                    raise RuntimeError("Invalid linker input")
                
                ln = f"jump {pos + offset} {spl[2]}"

            nl += 1
            tmp += ln + "\n"
        
        return tmp.strip(), nl

if __name__ == "__main__":
    l = Linker()
    print(l.link([
"""\
print 10
printflush message1


""",
"""\
print 20
printflush message1
jump 0 always _ _
""",
"""\
print 30
printflush message1
jump 0 always _ _"""
    ]))
