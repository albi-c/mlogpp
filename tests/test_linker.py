import unittest

from mlogpp.instruction import InstructionPrint, InstructionJump, Label
from mlogpp.linker import Linker


class LinkerTestCase(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(Linker.link([
            InstructionPrint(0),
            Label("test"),
            InstructionPrint(1),
            InstructionJump("test", "always", "_", "_"),
            InstructionPrint(2)
        ]), """\
print 0
print 1
jump 1 always _ _
print 2""")


if __name__ == '__main__':
    unittest.main()
