from .instruction import *


class Linker:
    """
    links generated code together
    """

    @staticmethod
    def link(code: Instructions | Instruction) -> str:
        """
        links generated code together
        """

        labels = {"start": 0}

        line = 0
        for ins in code.iter():
            generated = str(ins)
            if generated.strip():
                if generated.endswith(":"):
                    labels[generated[:-1]] = line
                else:
                    line += 1

        output_code = ""
        for ins in code.iter():
            generated = str(ins)
            if generated.endswith(":"):
                continue
            if generated.startswith("jump "):
                spl = generated.split(" ", 2)
                jump_to = labels.get(spl[1], -1)
                if jump_to >= line:
                    jump_to = 0
                output_code += spl[0] + " " + str(jump_to) + " " + spl[2] + "\n"
            else:
                output_code += generated + "\n"

        return output_code.strip()
