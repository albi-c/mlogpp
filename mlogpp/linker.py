from .instruction import *


class Linker:
    """
    Resolves labels.
    """

    @staticmethod
    def link(code: Instructions | Instruction) -> str:
        """
        Resolve labels.

        Args:
            code: The generated instructions.

        Returns:
            The code with resolved labels.
        """

        # label at the start of the code
        labels = {"start": 0}

        # find labels
        line = 0
        for ins in code.iter():
            # generate the instruction
            generated = str(ins)

            if generated.strip():
                # check if the line is a label
                if generated.endswith(":"):
                    labels[generated[:-1]] = line

                else:
                    line += 1

        output_code = ""
        for ins in code.iter():
            # generate the instruction
            generated = str(ins)

            # skip labels
            if generated.endswith(":"):
                continue

            # resolve jump addressed
            if generated.startswith("jump "):
                spl = generated.split(" ", 2)
                jump_to = labels.get(spl[1], -1)

                # wrap around to 0 if address is larger than last instruction
                if jump_to >= line:
                    jump_to = 0

                output_code += spl[0] + " " + str(jump_to) + " " + spl[2] + "\n"

            else:
                output_code += generated + "\n"

        return output_code.strip()
