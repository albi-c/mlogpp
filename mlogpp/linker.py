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
        label_count = 0
        tmp = ""
        for i, ln in enumerate(code.splitlines()):
            # is a label
            if ln.startswith("<"):
                labels[ln[1:]] = i - label_count
                label_count += 1
                continue

            tmp += ln + "\n"
        
        # resolve jumps
        code = ""
        for i, ln in enumerate(tmp.splitlines()):
            # is a jump
            if ln.startswith(">"):
                # jump data
                jd = ln[1:].split(" ")

                if len(jd) == 1:
                    # always jump
                    code += f"jump {labels[jd[0]]} always _ _\n"

                elif len(jd) == 4:
                    # conditional jump
                    code += f"jump {labels[jd[0]]} {jd[2]} {jd[1]} {jd[3]}\n"
                
                continue
            
            code += ln + "\n"
        
        lns = code.splitlines()
        n_lines = len(lns)
        for i, ln in enumerate(lns):
            # is a jump
            if ln.startswith("jump "):
                spl = ln.split(" ", 2)
                if int(spl[1]) >= n_lines:
                    spl[1] = "0"
                lns[i] = " ".join(spl)
        
        return "\n".join(lns)
