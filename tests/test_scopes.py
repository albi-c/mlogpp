import unittest

from mlogpp.scope import *


class ScopesTestCase(unittest.TestCase):
    def test_variables_functions(self):
        Scope.reset({})

        Scope.push("test_scope")

        self.assertEqual(Scope.scopes, [{}, {}, {}, {}, {}])
        self.assertEqual(Scope.names, ["<enum>", "<builtins>", "<config>", "<main>", "test_scope"])
        self.assertEqual(Scope.loops, [])
        self.assertEqual(Scope.functions, [])


if __name__ == '__main__':
    unittest.main()
