from collections import defaultdict

from .instruction import *


class Optimizer:
    Instructions = list[Instruction]

    @classmethod
    def optimize(cls, code: Instructions) -> Instructions:
        while cls._optimize_immediate_move(code):
            pass

        cls._remove_noops(code)

        return code

    @classmethod
    def _optimize_immediate_move(cls, code: Instructions) -> bool:
        """
        read __tmp0 cell1 0
        set x __tmp0

        read x cell1 0
        """

        uses = defaultdict(int)
        first_uses = {}

        for i, ins in enumerate(code):
            for j, param in enumerate(ins.params):
                uses[param] += 1
                if uses[param] == 1:
                    first_uses[param] = i, j

        found = False
        for i, ins in enumerate(code):
            if isinstance(ins, InstructionSet):
                if ins.params[1].startswith("__tmp"):
                    tmp = ins.params[1]
                    first = first_uses[tmp]
                    if uses[tmp] == 2 and i != first[0]:
                        code[first[0]].params[first[1]] = ins.params[0]
                        code[i] = InstructionNoop()
                        found = True

        return found

    @classmethod
    def _remove_noops(cls, code: Instructions):
        code[:] = [ins for ins in code if ins != InstructionNoop()]
