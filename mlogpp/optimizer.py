from __future__ import annotations

from collections import defaultdict
import math
import typing

from .instruction import *
from .operations import Operations


class Phi(Instruction):
    def __init__(self):
        BaseInstruction.__init__(self, "phi", tuple(), True)

    def __str__(self):
        # raise RuntimeError("Phi instruction must be converted")
        print("! Phi instruction must be converted !")
        return "PHI"


class Block(list):
    predecessors: set[Block]
    successors: set[Block]
    variables: dict[str, int]
    assignments: set[str]

    def __init__(self, code: typing.Iterable[Instruction]):
        super().__init__(code)

        self.predecessors = set()
        self.successors = set()
        self.variables = {}
        self.assignments = set()

    def __hash__(self):
        return hash(id(self))


class Optimizer:
    Instructions = list[Instruction]
    Blocks = list[Block]

    @classmethod
    def optimize(cls, code: Instructions) -> Instructions:
        cls._remove_noops(code)
        cls._optimize_jumps(code)

        cls._remove_noops(code)
        while cls._optimize_immediate_move(code):
            pass

        cls._remove_noops(code)

        blocks = cls._make_blocks(code)
        cls._eval_block_jumps(blocks)
        cls._find_assignments(blocks)
        for i, block in enumerate(blocks):
            print("BLOCK", i)
            print("PRE", len(block.predecessors), block.predecessors)
            print("SUC", len(block.successors), block.successors)
            print("ASSIGN", block.assignments)
            print("\n".join(map(str, block)))
            print()
        cls._make_ssa(blocks)
        code = cls._make_instructions(blocks)

        cls._remove_noops(code)
        cls._optimize_jumps(code)

        cls._remove_noops(code)
        while cls._optimize_immediate_move(code):
            pass

        cls._remove_noops(code)
        # cls._ExecutionOptimizer(code).optimize(1)

        cls._remove_noops(code)
        cls._remove_unused_variables(code)

        cls._remove_noops(code)
        return code

    @classmethod
    def _optimize_jumps(cls, code: Instructions):
        jumps = {ins.params[0] for ins in code if isinstance(ins, InstructionJump)}
        print(jumps)
        code[:] = [ins for i, ins in enumerate(code) if not isinstance(ins, Label) or (ins.params[0] in jumps)]

    @classmethod
    def _make_blocks(cls, code: Instructions) -> Blocks:
        blocks: Blocks = [[]]
        for ins in code:
            if isinstance(ins, Label):
                blocks.append([ins])

            elif isinstance(ins, InstructionJump):
                blocks[-1].append(ins)
                blocks.append([])

            else:
                blocks[-1].append(ins)

        return [Block(block) for block in blocks if len(block) > 0]

    @classmethod
    def _find_assignments(cls, code: Blocks):
        for block in code:
            for ins in block:
                for o in ins.outputs:
                    block.assignments.add(ins.params[o])

    @classmethod
    def _make_instructions(cls, code: Blocks) -> Instructions:
        return [ins for block in code for ins in block]

    @classmethod
    def _eval_block_jumps(cls, code: Blocks):
        """
        Evaluate jumps to remove dead blocks and list predecessors.
        """

        if len(code) == 0:
            return

        labels = {lab.params[0]: i for i, block in enumerate(code) for lab in block if isinstance(lab, Label)}

        used = set()
        cls._eval_block_jumps_internal(code, labels, 0, used)

        code[:] = [block for i, block in enumerate(code) if i in used]
        for block in code:
            block.predecessors = {pre for pre in block.predecessors if pre in code}
            for pre in block.predecessors:
                pre.successors.add(block)

    @classmethod
    def _eval_block_jumps_internal(cls, code: Blocks, labels: dict[str, int], i: int, used: set[int], from_: int = None):
        if i >= len(code):
            return

        if from_ is not None:
            code[i].predecessors.add(code[from_])

        if i in used:
            return
        used.add(i)

        for ins in code[i]:
            if isinstance(ins, InstructionJump):
                if ins.params[1] == "always":
                    cls._eval_block_jumps_internal(code, labels, labels[ins.params[0]], used, i)
                    return

                else:
                    cls._eval_block_jumps_internal(code, labels, labels[ins.params[0]], used, i)
                    cls._eval_block_jumps_internal(code, labels, i + 1, used, i)
                    return

        cls._eval_block_jumps_internal(code, labels, i + 1, used, i)

    @classmethod
    def _make_ssa(cls, code: Blocks):
        # TODO: insert phi instructions

        variables = defaultdict(int)
        for block in code:
            for ins in block:
                for i in ins.inputs:
                    if ins.params[i] in variables:
                        ins.params[i] += ":" + str(variables[ins.params[i]])
                for o in ins.outputs:
                    variables[ins.params[o]] += 1
                    ins.params[o] += ":" + str(variables[ins.params[o]])

    @classmethod
    def _optimize_immediate_move(cls, code: Instructions) -> bool:
        """
        Remove single use temporary variables that are immediately moved into a named one.

        read __tmp0 cell1 0
        set x __tmp0

        read x cell1 0
        """

        uses = defaultdict(int)
        first_uses = {}

        for i, ins in enumerate(code):
            for j in ins.inputs + ins.outputs:
                param = ins.params[j]
                uses[param] += 1
                if uses[param] == 1:
                    first_uses[param] = (i, j)

        for i, ins in enumerate(code):
            if isinstance(ins, InstructionSet):
                tmp = ins.params[1]
                first = first_uses[tmp]
                if uses[tmp] == 2 and i != first[0]:
                    code[first[0]].params[first[1]] = ins.params[0]
                    code[i] = InstructionNoop()
                    return True

        return False

    @classmethod
    def _remove_unused_variables(cls, code: Instructions):
        uses = defaultdict(int)
        first_uses = {}

        for i, ins in enumerate(code):
            for j in ins.inputs + ins.inputs:
                param = ins.params[j]
                uses[param] += 1
                if uses[param] == 1:
                    first_uses[param] = i, j

        for i, ins in enumerate(code):
            if not ins.side_effects and len(ins.outputs) > 0:
                if not any(uses.get(ins.params[i], 0) > 1 for i in ins.outputs):
                    code[i] = InstructionNoop()

    @classmethod
    def _remove_noops(cls, code: Instructions):
        code[:] = [ins for ins in code if ins != InstructionNoop()]

    class _ExecutionOptimizer:
        """
        Precalculate values.

        set y 3
        op add x 1 y
        print x

        set y 3
        set x 4
        print 4
        """

        class Undecided(Exception):
            pass

        Variable = int | float | str | bool | None
        Instructions = list[Instruction]

        code: Instructions
        variables: dict[str, Variable]
        labels: dict[str, int]

        def __init__(self, code: Instructions):
            self.code = code

        def _reset(self):
            self.variables = {
                "true": 1,
                "false": 0,
                "null": "null",
                "@counter": 0
            }
            self.labels = {lab.name: i for i, lab in enumerate(self.code) if isinstance(lab, Label)}

        def __getitem__(self, name: str) -> Variable:
            name = str(name)

            try:
                val = float(self.variables[name])
                if val.is_integer():
                    val = int(val)
                return val
            except (ValueError, KeyError):
                pass

            if name.startswith("\"") and name.endswith("\""):
                return name

            val = self.variables.get(name)
            if isinstance(val, str) and val in self.variables and self.variables[val] != val:
                return self[val]

            return val

        def __setitem__(self, name: str, value: Variable):
            name = str(name)

            self.variables[name] = value

        def __delitem__(self, name: str):
            name = str(name)

            if name in self.variables:
                del self.variables[name]

        def optimize(self, passes: int):
            for _ in range(passes):
                try:
                    self._reset()
                    self._optimize()

                except Optimizer._ExecutionOptimizer.Undecided:
                    print("END", self.code[self["@counter"] - 1])
                    pass

                else:
                    print("SUCCESS")

        def _optimize(self):
            while isinstance(self["@counter"], int) and self["@counter"] < len(self.code):
                ins = self.code[self["@counter"]]
                self["@counter"] += 1

                if isinstance(ins, Label):
                    continue

                for inp in ins.inputs:
                    if ins.params[inp] == "@counter":
                        continue

                    if (val := self[ins.params[inp]]) is not None:
                        ins.params[inp] = val

                if (out := self._eval_ins(ins)) is not None:
                    for i, o in enumerate(ins.outputs):
                        print(ins, out, ins.params[o], out[i])
                        self[ins.params[o]] = out[i]

        def _eval_ins(self, ins: Instruction) -> list[Variable] | None:
            if isinstance(ins, InstructionSet):
                if (val := self[ins.params[1]]) is not None:
                    return [val]

                else:
                    return [ins.params[1]]

            elif isinstance(ins, InstructionJump):
                print(ins)
                if ins.params[1] == "always":
                    self["@counter"] = self.labels[ins.params[0]]

                # elif ins.params[1] in Operations.JUMP_PRECALC:
                #     try:
                #         a = float(ins.params[2])
                #         if a.is_integer():
                #             a = int(a)
                #
                #         b = float(ins.params[3])
                #         if b.is_integer():
                #             b = int(b)
                #
                #         if Operations.JUMP_PRECALC[ins.params[1]](a, b):
                #             self["@counter"] = self.labels[ins.params[0]]
                #
                #         return None
                #
                #     except (ValueError, TypeError):
                #         raise self.Undecided()

                else:
                    raise self.Undecided()

            elif isinstance(ins, InstructionOp):
                if ins.params[0] in Operations.PRECALC:
                    a = None
                    try:
                        a = float(ins.params[2])
                        if a.is_integer():
                            a = int(a)
                    except ValueError:
                        pass

                    if a is not None:
                        result = None

                        try:
                            result = float(Operations.PRECALC[ins.params[0]](a, None))

                        except (ArithmeticError, TypeError):
                            b = None
                            try:
                                b = float(ins.params[3])
                                if b.is_integer():
                                    b = float(b)
                            except ValueError:
                                pass

                            if b is not None:
                                try:
                                    result = float(Operations.PRECALC[ins.params[0]](a, b))

                                except (ArithmeticError, TypeError):
                                    pass

                        if result is not None:
                            if result.is_integer():
                                result = int(result)
                            return [result]

                raise self.Undecided()

            elif isinstance(ins, InstructionNoop):
                return None

            else:
                for i in ins.outputs:
                    del self[ins.params[i]]

                # TODO
                raise self.Undecided()

            return None
