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
        self.assertEqual(Gen.LOCALS_STACK, [])

    def test_locals(self):
        Gen.push_locals()

        Gen.add_locals(["a", "b", "c"])
        self.assertTrue(Gen.is_local("a"))
        self.assertTrue(Gen.is_local("b"))
        self.assertFalse(Gen.is_local("d"))

        Gen.add_locals(["c", "d", "e"])
        self.assertTrue(Gen.is_local("c"))
        self.assertTrue(Gen.is_local("e"))

        Gen.push_locals()

        self.assertFalse(Gen.is_local("d"))

        Gen.reset()

        self.assertEqual(Gen.LOCALS_STACK, [])


if __name__ == '__main__':
    unittest.main()
