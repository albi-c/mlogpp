import re, os

PRE_REGEXES = {
    "CONST": re.compile(r"^const [a-zA-Z_@][a-zA-Z_0-9]* = .+$")
}

class Preprocessor:
    def preprocess(self, code: str) -> str:
        tmp2 = code
        
        # Resolve includes and labels
        included = []
        while True:
            tmp = ""
            found = False
            for ln in tmp2.splitlines():
                st = ln.strip()
                if st.startswith("%"):
                    fn = st[1:].strip()

                    if not os.path.isfile(fn):
                        raise RuntimeError(f"Cannot import file \"{fn}\"")
                    
                    if fn in included:
                        raise RuntimeError(f"File \"{fn}\" is already included")
                    
                    included.append(fn)
                    
                    with open(fn, "r") as f:
                        data = f.read()
                    
                    tmp += f"\n{data}\n"

                    found = True
                    continue
                elif st.startswith(">") or st.startswith("<"):
                    ln = "." + st
                
                tmp += ln + "\n"
            
            if not found:
                break

            tmp2 = tmp

        tmp = tmp.strip(" \t\n")

        # Find constanrs
        tmp2 = ""
        const_table = {}
        for ln in tmp.splitlines():
            if PRE_REGEXES["CONST"].fullmatch(ln):
                spl = ln.split(" ", 3)
                if spl[1] in const_table:
                    raise RuntimeError(f"Redefining a constant \"{spl[1]}\"")
                const_table[spl[1]] = spl[3]
                continue

            tmp2 += ln + "\n"
        
        # Resolve raw code lines
        table = str.maketrans({"\n": "\\n", "\"":"\\\"", "\\":"\\\\"})
        tmp = ""
        for ln in tmp2.splitlines():
            if ln.strip().startswith("."):
                ln = f".\"{ln.strip()[1:].translate(table)}\""
            
            for k, v in const_table.items():
                ln = re.sub("(?<=[^\"']){}(?=\\\\?[^\"'])".format(k), v, ln)
            
            tmp += ln + "\n"
        
        # Remove leading and trailing whitespaces
        tmp2 = ""
        in_str = False
        prev = ""
        for c in tmp:
            if c == "\"" and prev != "\\":
                in_str = not in_str
            
            if (c != " " and c != "\t") or in_str:
                tmp2 += c
            
            prev = c
        
        # Remove comments
        tmp = ""
        for ln in tmp2.splitlines():
            if not ln.startswith("#") and ln:
                tmp += ln + "\n"

        return tmp
