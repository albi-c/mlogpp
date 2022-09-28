import unittest

from mlogpp.linker import *


class GeneratorTestCase(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(Linker.link([Instructions([
            MInstruction(MInstructionType.PRINT, ["0"]),
            MppInstructionLabel("test"),
            MInstruction(MInstructionType.PRINT, ["1"]),
            MppInstructionJump("test"),
            MInstruction(MInstructionType.PRINT, ["2"])
        ])]), """\
print 0
test:
print 1
jump test always _ _
print 2""")

    def test_joining(self):
        self.assertEqual(Linker.link([Instructions([
            MInstruction(MInstructionType.PRINT, ["0"]),
            MppInstructionLabel("lab1"),
            MInstruction(MInstructionType.PRINT, ["1"]),
            MppInstructionJump("lab1")
        ]), Instructions([
            MInstruction(MInstructionType.PRINT, ["2"]),
            MppInstructionLabel("lab2"),
            MInstruction(MInstructionType.PRINT, ["3"]),
            MppInstructionJump("lab1"),
            MppInstructionJump("lab2"),
            MInstruction(MInstructionType.PRINT, ["4"])
        ])]), """\
print 0
lab1:
print 1
jump lab1 always _ _
print 2
lab2:
print 3
jump lab1 always _ _
jump lab2 always _ _
print 4""")


if __name__ == '__main__':
    unittest.main()
