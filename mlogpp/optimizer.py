import re
from collections import defaultdict

from .functions import PRECALC, JC_REPLACE
from .instruction import *
from .value import *


class Optimizer:
    """
    Optimizes generated code.
    """

    @staticmethod
    def optimize(code: Instructions) -> Instructions:
        """
        Optimize generated code.

        Args:
            code: The code to be optimized.

        Returns:
             The optimized code.
        """

        # optimize ten times
        for _ in range(10):
            # look ahead 10 lines
            for i in range(1, 10):
                # optimize single use variables
                while (cf := Optimizer._single_use_optimize(code, i))[1]:
                    code = cf[0]

                # precalculate values
                while (cf := Optimizer._precalculate_optimize(code))[1]:
                    code = cf[0]

                # reduce jumps
                while (cf := Optimizer._jump_optimize(code))[1]:
                    code = cf[0]

        code = Optimizer._remove_noops(code)
        code = Optimizer._dead_code_optimize(code)
        return code

    @staticmethod
    def _remove_noops(code: Instructions) -> Instructions:
        """
        Remove noops from code.

        Args:
            code: The input code.

        Returns:
            The code without noops.
        """

        return Instructions([ins for ins in code.iter() if not isinstance(ins, NoopInstruction)])

    @staticmethod
    def _single_use_optimize(code: Instructions, forward: int = 1) -> tuple[Instructions, bool]:
        """
        Optimize single use temporary variables.

        Args:
            code: The code to be optimized.
            forward: How many lines forward should be looked.

        Returns:
            The optimized code.
        """

        code = code.copy()

        # count uses of variables
        uses = defaultdict(int)
        input_uses = defaultdict(int)
        output_uses = defaultdict(int)
        for ins in code.iter():
            for var in ins.inputs():
                if var.startswith("@"):
                    continue

                input_uses[var] += 1
                uses[var] += 1

            for var in ins.outputs():
                if var.startswith("@"):
                    continue

                output_uses[var] += 1
                uses[var] += 1

        found = False
        for i, ins in enumerate(code.iter()):
            # check if the instruction is a Mindustry one
            if isinstance(ins, MInstruction):
                fi = i + forward

                # check if there is an instruction `forward` lines forward
                if fi < len(code):
                    cfi = code[fi]

                    match ins:
                        # assignment to a variable
                        case MInstruction(MInstructionType.SET, [name, value]):
                            if name.startswith("@") or value.startswith("@"):
                                continue

                            if input_uses[name] == 0:
                                code[i] = NoopInstruction()
                                found = True

                            elif uses[name] == 2:
                                if name in cfi.variables():
                                    code[i] = NoopInstruction()
                                    cfi.param_replace(name, value)
                                    found = True

                        # getlink to a variable
                        case MInstruction(MInstructionType.GETLINK, [name, _]):
                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses[name] == 2 and name.startswith("__tmp") and cfi.params[1] == name:
                                ins.params[0] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

                        # operation to a variable
                        case MInstruction(MInstructionType.OP, [op, result, op1, op2]):
                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses[result] == 2 and result.startswith("__tmp") and cfi.params[1] == result:
                                ins.params[1] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

                            if isinstance(cfi, MppInstructionOJump) and uses[result] == 2 and \
                                    result.startswith("__tmp") and cfi.op1 == result and \
                                    cfi.op == "equal" and cfi.op2 in ("0", "false"):

                                if op in JC_REPLACE:
                                    code[i] = NoopInstruction()
                                    cfi.op = JC_REPLACE[op]
                                    cfi.op1 = op1
                                    cfi.op2 = op2
                                    found = True

                        # sensor to a variable
                        case MInstruction(MInstructionType.SENSOR, [result, _, _]):
                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses[result] == 2 and result.startswith("__tmp") and cfi.params[1] == result:
                                ins.params[0] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

                        # radar / uradar to a variable
                        case MInstruction(MInstructionType.URADAR, [_, _, _, _, _, _, result]) | \
                             MInstruction(MInstructionType.RADAR, [_, _, _, _, _, _, result]):

                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses[result] == 2 and result.startswith("__tmp") and cfi.params[1] == result:
                                ins.params[6] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

                        # read to a variable
                        case MInstruction(MInstructionType.READ, [result, _, _]):
                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses[result] == 2 and result.startswith("__tmp") and cfi.params[1] == result:
                                ins.params[0] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

        return Optimizer._remove_noops(code), found

    @staticmethod
    def _precalculate_optimize(code: Instructions) -> tuple[Instructions, bool]:
        """
        Precalculate numerical values.

        Args:
            code: The code to be optimized.

        Returns:
            The optimized code.
        """

        code = code.copy()

        found = False
        for i, ins in enumerate(code.iter()):
            if isinstance(ins, MInstruction) and ins.type == MInstructionType.OP:
                if (val := Optimizer._precalc(ins.params[0], ins.params[2], ins.params[3])) is not None:
                    code[i] = MInstruction(MInstructionType.SET, [ins.params[1], val])
                    found = True

        return code, found

    @staticmethod
    def _precalc(op: str, a: str, b: str) -> int | float | None:
        """
        Precalculate a value.

        Args:
            op: The operator.
            a: The first operand.
            b: The second operand.

        Returns:
            The precalculated value.
        """

        if op not in PRECALC:
            return None

        try:
            # check if the parameters can be converted to numbers, convert to integers if whole
            a = float(a)
            if a.is_integer():
                a = int(a)
            b = float(b)
            if b.is_integer():
                b = int(b)
        except ValueError:
            return None
        else:
            try:
                val = float(PRECALC[op](a, b))
                if val.is_integer():
                    val = int(val)

                return val
            except ArithmeticError:
                return None

    @staticmethod
    def _jump_optimize(code: Instructions) -> tuple[Instructions, bool]:
        found = False

        labels = {}
        prev = None
        for ins in enumerate(code.iter()):
            if isinstance(prev, MppInstructionLabel):
                labels[prev.name] = ins
            prev = ins

        for i, ins in enumerate(code.iter()):
            if isinstance(ins, MppInstructionJump | MppInstructionOJump):
                if (target := labels.get(ins.label)) is None:
                    continue

                if isinstance(target, MppInstructionJump):
                    ins.label = target.label
                    found = True

                elif isinstance(target, MppInstructionOJump) and target.op in PRECALC:
                    if (val := Optimizer._precalc(target.op, target.op1, target.op2)) is not None and val:
                        ins.label = target.label
                        found = True

        return code, found

    @staticmethod
    def _dead_code_optimize(code: Instructions) -> Instructions:
        labels = {ins.name: i for i, ins in enumerate(code.iter()) if isinstance(ins, MppInstructionLabel)}
        labels["start"] = 0
        live = set()
        Optimizer._find_live_code(code, live, 0, labels)

        return Instructions([ins for i, ins in enumerate(code.iter()) if i in live])

    @staticmethod
    def _find_live_code(code: Instructions, live: set[int], i: int, labels: dict[str, int]):
        if i in live or i >= len(code.iter()):
            return

        for ins in code.iter()[i:]:
            live.add(i)
            if isinstance(ins, MppInstructionJump):
                target = labels.get(ins.label)
                if target is None:
                    InternalError.label_not_found(ins.label)
                Optimizer._find_live_code(code, live, target, labels)

                if i >= 1:
                    n = code.iter()[i - 1]
                    if isinstance(n, MInstruction) and n.type == MInstructionType.OP and n.params[0] == "add" and \
                            n.params[1].endswith("_ret") and n.params[2] == "@counter":

                        i += 1
                        continue

                return
            elif isinstance(ins, MppInstructionOJump):
                target = labels.get(ins.label)
                if target is None:
                    InternalError.label_not_found(ins.label)
                Optimizer._find_live_code(code, live, target, labels)
            i += 1
