import unittest

from mlogpp.generator import Gen
from mlogpp.instruction import InstructionNoop


class GeneratorTestCase(unittest.TestCase):
    def test_variables(self):
        Gen._tmp_index = 0

        self.assertEqual(Gen.tmp(), "__tmp1")
        self.assertEqual(Gen.tmp(), "__tmp2")

    def test_reset(self):
        Gen.tmp()
        Gen.emit(InstructionNoop())

        Gen.reset()

        # should not reset to avoid name collisions
        self.assertNotEqual(Gen._tmp_index, 0)

        self.assertEqual(Gen._instructions, [])

    def test_emit(self):
        Gen.reset()

        Gen.emit(InstructionNoop())

        self.assertEqual(Gen.get(), [InstructionNoop()])


if __name__ == '__main__':
    unittest.main()
