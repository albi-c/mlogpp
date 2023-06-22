from .instruction import Instruction


class Linker:
    """
    Resolves labels.
    """

    EMIT_LABELS: bool = False

    @classmethod
    def link(cls, code: list[Instruction]) -> str:
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
        for ins in code:
            # generate the instruction
            generated = str(ins).strip()

            if generated:
                # check if the line is a label
                if generated.endswith(":"):
                    labels[generated[:-1]] = line

                else:
                    line += 1

        # generate instructions and skip labels
        code = [ins for ins in (str(ins) for ins in code) if not ins.endswith(":") or cls.EMIT_LABELS]

        output_code = ""
        offset = 0
        for i, generated in enumerate(code):
            # resolve jump addressed
            if generated.startswith("jump "):
                spl = generated.split(" ", 2)
                jump_to = labels.get(spl[1])
                if jump_to is None:
                    InternalError.label_not_found(spl[1])

                # wrap around to 0 if address is larger than last instruction
                if jump_to >= line:
                    jump_to = 0

                if i == len(code) - 1 and jump_to == 0:
                    continue

                if jump_to == i + 1:
                    offset += 1
                    continue

                if cls.EMIT_LABELS:
                    output_code += generated + "\n"

                else:
                    output_code += spl[0] + " " + str(jump_to - offset) + " " + spl[2] + "\n"

            else:
                output_code += generated + "\n"

        return output_code.strip()
