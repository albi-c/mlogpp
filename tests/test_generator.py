import unittest

from mlogpp.generator import Var, Gen


class VariableTestCase(unittest.TestCase):
    def test_properties(self):
        var = Var("test_variable", True)

        self.assertEqual(var.n, "test_variable")
        self.assertTrue(var.c)
        self.assertFalse(var.nc)

        self.assertFalse(var.e(False).c)
        self.assertTrue(var.e(False).nc)
        self.assertFalse(var.e(True).nc)
        self.assertTrue(var.e(True).c)


class GeneratorTestCase(unittest.TestCase):
    def test_variables(self):
        Gen.reset()

        self.assertEqual(Gen.temp_var().n, "__tmp0")
        self.assertEqual(Gen.temp_lab(), "__tmp0")
        self.assertEqual(Gen.temp_var().n, "__tmp1")
        self.assertEqual(Gen.temp_lab(), "__tmp1")

    def test_reset(self):
        Gen.reset()

        self.assertEqual(Gen.VAR_COUNT, 0)
        self.assertEqual(Gen.LAB_COUNT, 0)
        self.assertEqual(Gen.GLOBALS_STACK, [])

    def test_globals(self):
        Gen.push_globals()

        Gen.add_globals(["a", "b", "c"])
        self.assertTrue(Gen.is_global("a"))
        self.assertTrue(Gen.is_global("b"))
        self.assertFalse(Gen.is_global("d"))

        Gen.add_globals(["c", "d", "e"])
        self.assertTrue(Gen.is_global("c"))
        self.assertTrue(Gen.is_global("e"))

        Gen.push_globals()

        self.assertFalse(Gen.is_global("d"))

        Gen.reset()

        self.assertEqual(Gen.GLOBALS_STACK, [])


if __name__ == '__main__':
    unittest.main()
