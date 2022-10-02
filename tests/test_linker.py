import unittest

from mlogpp.linker import *


class LinkerTestCase(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(Linker.link(Instructions([
            MInstruction(MInstructionType.PRINT, [0]),
            MppInstructionLabel("test"),
            MInstruction(MInstructionType.PRINT, [1]),
            MppInstructionJump("test"),
            MInstruction(MInstructionType.PRINT, [2])
        ])), """\
print 0
print 1
jump 1 always _ _
print 2""")


if __name__ == '__main__':
    unittest.main()
