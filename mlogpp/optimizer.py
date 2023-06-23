from __future__ import annotations

from collections import defaultdict
import typing
import itertools

from .instruction import *
from .operations import Operations
from . import builtins


class Phi(Instruction):
    variable: str
    output: str
    inputs_: set[Block]

    def __init__(self, variable: str, output: str, inputs: set[Block]):
        BaseInstruction.__init__(self, "phi", (), True)

        self.variable = variable
        self.output = output
        self.inputs_ = inputs

    def __str__(self):
        raise RuntimeError("Phi instruction must be converted")

BaseInstruction.Builtins["phi"] = builtins.native_function_value(Phi, [])


class Block(list[Instruction]):
    predecessors: set[Block]
    successors: set[Block]
    variables: dict[str, int]
    assignments: set[str]
    is_ssa: bool
    add_phi: list[Instruction]

    def __init__(self, code: typing.Iterable[Instruction]):
        super().__init__(code)

        self.predecessors = set()
        self.successors = set()
        self.variables = {}
        self.assignments = set()
        self.is_ssa = False
        self.add_phi = []

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
        cls._optimize_block_jumps(blocks)
        cls._make_ssa(blocks)
        while cls._propagate_constants(blocks) | cls._precalculate_values(blocks):
            pass
        cls._resolve_ssa(blocks)
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
        code[:] = [ins for i, ins in enumerate(code) if not isinstance(ins, Label) or (ins.params[0] in jumps)]

        labels = {ins.params[0]: i for i, ins in enumerate(code) if isinstance(ins, Label)}
        code[:] = [ins if not isinstance(ins, InstructionJump) or
                          labels[ins.params[0]] != i else InstructionNoop() for i, ins in enumerate(code)]

    @classmethod
    def _make_blocks(cls, code: Instructions) -> Blocks:
        blocks: list[Optimizer.Instructions] = [[]]
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
    def _optimize_block_jumps(cls, code: Blocks):
        labels = {lab.params[0]: i for i, block in enumerate(code) for lab in block if isinstance(lab, Label)}
        for i, block in enumerate(code):
            if isinstance(block[-1], InstructionJump) and labels[block[-1].params[0]] == i + 1:
                block.pop(-1)

    @classmethod
    def _make_ssa(cls, code: Blocks):
        if len(code) > 0:
            cls._make_ssa_internal(code[0], {})

    @classmethod
    def _make_ssa_internal(cls, block: Block, variables: dict[str, int]):
        if block.is_ssa:
            return

        block.variables = variables.copy()

        phi_required: dict[str, set[Block]] = {}
        for a, b in itertools.combinations(block.predecessors, 2):
            for common in a.assignments & b.assignments:
                if common in phi_required:
                    phi_required[common] |= {a, b}
                else:
                    phi_required[common] = {a, b}

        for name, blocks in phi_required.items():
            block.variables[name] = block.variables.get(name, 0) + 1
            block.insert(0, Phi(name, f"{name}:{block.variables[name]}", blocks))

        for ins in block:
            for i in ins.inputs:
                inp = ins.params[i]
                if inp in block.variables:
                    ins.params[i] += ":" + str(block.variables[inp])
            for o in ins.outputs:
                out = ins.params[o]
                block.variables[out] = block.variables.get(out, 0) + 1
                ins.params[o] += ":" + str(block.variables[out])

        block.is_ssa = True

        for suc in block.successors:
            cls._make_ssa_internal(suc, block.variables)

    @classmethod
    def _propagate_constants(cls, code: Blocks) -> bool:
        constants: dict[str, str] = {}

        for block in code:
            for ins in block:
                if isinstance(ins, InstructionSet):
                    constants[ins.params[0]] = ins.params[1]

        found = False
        for block in code:
            for ins in block:
                for i in ins.inputs:
                    if ins.params[i] in constants:
                        ins.params[i] = constants[ins.params[i]]
                        found = True

        return found

    @classmethod
    def _precalculate_values(cls, code: Blocks) -> bool:
        found = False
        for block in code:
            for i, ins in enumerate(block):
                if isinstance(ins, InstructionOp):
                    if (ins.params[0] == "sub" and ins.params[2] == ins.params[3]) or \
                            (ins.params[0] == "mul" and (ins.params[2] == "0" or ins.params[3] == "0")) or \
                            (ins.params[0] in ("div", "idiv") and ins.params[2] == "0") or \
                            (ins.params[0] == "and" and (ins.params[2] == "0" or ins.params[3] == "0")):

                        block[i] = InstructionSet(ins.params[1], 0)
                        found = True

                    elif ins.params[0] in ("add", "or", "xor") and ins.params[2] == "0":
                        block[i] = InstructionSet(ins.params[3], 0)
                        found = True

                    elif ins.params[0] in ("add", "or", "xor") and ins.params[3] == "0":
                        block[i] = InstructionSet(ins.params[2], 0)
                        found = True

                    elif ins.params[0] in ("shr", "shl") and ins.params[3] == "0":
                        block[i] = InstructionSet(ins.params[2], 0)
                        found = True

                    elif ins.params[0] in Operations.PRECALC:
                        try:
                            a = float(ins.params[2])
                            if a.is_integer():
                                a = int(a)
                            b = float(ins.params[3])
                            if b.is_integer():
                                b = int(b)

                            result = float(Operations.PRECALC[ins.params[0]](a, b))
                            if result.is_integer():
                                result = int(result)

                            block[i] = InstructionSet(ins.params[1], result)
                            found = True

                        except (ArithmeticError, ValueError, TypeError):
                            pass

        return found

    @classmethod
    def _resolve_ssa(cls, code: Blocks):
        for block in code:
            for i, ins in enumerate(block):
                if isinstance(ins, Phi):
                    for b in ins.inputs_:
                        b.add_phi.append(InstructionSet(ins.output, f"{ins.variable}:{b.variables[ins.variable]}"))
                    block[i] = InstructionNoop()

        for block in code:
            if isinstance(block[-1], InstructionJump):
                block[-1:] = block.add_phi + block[-1:]

            else:
                block += block.add_phi

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
                if not any(uses.get(ins.params[j], 0) > 1 for j in ins.outputs):
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
