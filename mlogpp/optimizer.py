import re

from .functions import PRECALC, JC_REPLACE
from .instruction import *
from .value import *


class Optimizer:
    """
    optimizes generated code
    """

    @staticmethod
    def optimize(code: Instructions) -> Instructions:
        """
        optimize generated code
        """

        for _ in range(10):
            for i in range(1, 10):
                while (cf := Optimizer._single_use(code, i))[1]:
                    code = cf[0]
                while (cf := Optimizer._precalculate_optimize(code))[1]:
                    code = cf[0]

        return code

    @staticmethod
    def _remove_noops(code: Instructions) -> Instructions:
        return Instructions([ins for ins in code.iter() if not isinstance(ins, NoopInstruction)])

    @staticmethod
    def _single_use(code: Instructions, forward: int = 1) -> tuple[Instructions, bool]:
        """
        optimize single use temporary variables
        """

        code = code.copy()

        uses = {}
        for ins in code.iter():
            for var in ins.variables():
                if var.startswith("@"):
                    continue

                if var not in uses:
                    uses[var] = 0
                uses[var] += 1

        found = False
        for i, ins in enumerate(code.iter()):
            if isinstance(ins, MInstruction):
                fi = i + forward

                if fi < len(code):
                    cfi = code[fi]
                    match ins:
                        case MInstruction(MInstructionType.SET, [name, value]):
                            if name.startswith("@") or value.startswith("@"):
                                continue

                            if uses.get(name, 0) == 1:
                                code[i] = NoopInstruction()
                                found = True

                            elif uses.get(name, 0) == 2:
                                if name in cfi.variables():
                                    code[i] = NoopInstruction()
                                    cfi.param_replace(name, value)
                                    found = True

                        case MInstruction(MInstructionType.GETLINK, [name, _]):
                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses.get(name, 0) == 2 and name.startswith("__tmp") and cfi.params[1] == name:
                                ins.params[0] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

                        case MInstruction(MInstructionType.OP, [op, result, op1, op2]):
                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses.get(result, 0) == 2 and result.startswith("__tmp") and cfi.params[1] == result:
                                ins.params[1] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

                            if isinstance(cfi, MppInstructionOJump) and uses.get(result, 0) == 2 and \
                                    result.startswith("__tmp") and cfi.op1 == result and \
                                    cfi.op == "equal" and cfi.op2 in ("0", "false"):

                                if op in JC_REPLACE:
                                    code[i] = NoopInstruction()
                                    cfi.op = JC_REPLACE[op]
                                    cfi.op1 = op1
                                    cfi.op2 = op2
                                    found = True

                        case MInstruction(MInstructionType.SENSOR, [result, _, _]):
                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses.get(result, 0) == 2 and result.startswith("__tmp") and cfi.params[1] == result:
                                ins.params[0] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

                        case MInstruction(MInstructionType.URADAR, [_, _, _, _, _, _, result]) | \
                                MInstruction(MInstructionType.RADAR, [_, _, _, _, _, _, result]):

                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses.get(result, 0) == 2 and result.startswith("__tmp") and cfi.params[1] == result:
                                ins.params[6] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

                        case MInstruction(MInstructionType.READ, [result, _, _]):
                            if isinstance(cfi, MInstruction) and cfi.type == MInstructionType.SET and \
                                    uses.get(result, 0) == 2 and result.startswith("__tmp") and cfi.params[1] == result:
                                ins.params[0] = cfi.params[0]
                                code[fi] = NoopInstruction()
                                found = True

        return Optimizer._remove_noops(code), found

    @staticmethod
    def _precalculate_optimize(code: Instructions) -> tuple[Instructions, bool]:
        """
        precalculate values where possible
        """

        code = code.copy()

        found = False
        for i, ins in enumerate(code.iter()):
            if isinstance(ins, MInstruction) and ins.type == MInstructionType.OP and ins.params[0] in PRECALC:
                try:
                    a = float(ins.params[2])
                    if a.is_integer():
                        a = int(a)
                    b = float(ins.params[3])
                    if b.is_integer():
                        b = int(b)
                except ValueError:
                    continue
                else:
                    try:
                        code[i] = MInstruction(MInstructionType.SET, [ins.params[1], Optimizer._precalc(ins.params[0], a, b)])
                        found = True
                    except ArithmeticError:
                        continue

        return code, found

    @staticmethod
    def _precalc(op: str, a: int | float, b: int | float) -> int | float:
        val = float(PRECALC[op](a, b))
        if val.is_integer():
            val = int(val)
        return val
