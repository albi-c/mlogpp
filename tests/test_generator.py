import unittest

from mlogpp.generator import Gen
from mlogpp.value import Type


class GeneratorTestCase(unittest.TestCase):
    def test_variables(self):
        Gen.reset()

        self.assertEqual(Gen.temp_var(Type.NUM).name, "__tmp0")
        self.assertEqual(Gen.temp_lab(), "__tmp0")
        self.assertEqual(Gen.temp_var(Type.NUM).name, "__tmp1")
        self.assertEqual(Gen.temp_lab(), "__tmp1")

    def test_reset(self):
        Gen.reset()

        self.assertEqual(Gen.VAR_COUNT, 0)
        self.assertEqual(Gen.LAB_COUNT, 0)


if __name__ == '__main__':
    unittest.main()
