from .instruction import *


class Linker:
    """
    links generated code together
    """

    @staticmethod
    def link(codes: list[Instructions | Instruction]) -> str:
        """
        links generated code together
        """

        labels = {"start": 0}

        line = 0
        for code_block in codes:
            for ins in code_block.iter():
                generated = str(ins)
                if generated.strip():
                    if generated.endswith(":"):
                        labels[generated[:-1]] = line
                    else:
                        line += 1

        code = ""
        for code_block in codes:
            for ins in code_block.iter():
                generated = str(ins)
                if generated.endswith(":"):
                    continue
                if generated.startswith("jump "):
                    spl = generated.split(" ", 2)
                    jump_to = labels.get(spl[1], -1)
                    if jump_to >= line:
                        jump_to = 0
                    code += spl[0] + " " + str(jump_to) + " " + spl[2] + "\n"
                else:
                    code += generated + "\n"

        return code.strip()
