import unittest

from mlogpp.generator import *


class MyTestCase(unittest.TestCase):
    def test_var(self):
        var = Var("test_variable", True)

        self.assertEqual(var.n, "test_variable")
        self.assertTrue(var.c)
        self.assertFalse(var.nc)

        self.assertEqual()


if __name__ == '__main__':
    unittest.main()
