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

        code = ""
        for code_block in codes:
            for ins in code_block.iter():
                code += str(ins) + "\n"

        return code.strip()
