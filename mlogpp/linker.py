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

        code = "start:\n"
        for code_block in codes:
            for ins in code_block.iter():
                generated = str(ins)
                if generated.strip():
                    code += generated + "\n"

        if code.count("jump start ") == 0:
            code = code.split("\n", 1)[1]

        return code.strip()
