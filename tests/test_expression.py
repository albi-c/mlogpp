import unittest

from mlogpp.expression import Expression
from mlogpp.util import Position


class ExpressionTestCase(unittest.TestCase):
    def test_expression(self):
        pos = Position(0, 0, 0, "<test>", "<test>")
        self.assertEqual(Expression.exec(pos, 'n=3\n"a"*(10//n+2)'), [None, "aaaaa"])
        self.assertEqual(Expression.exec(pos, '"a" if 2 > 3 else "b"'), ["b"])
        self.assertEqual(Expression.exec(pos, "''.join(map(str, [x**2 for x in range(10) if x % 2 == 0]))"), ["04163664"])


if __name__ == '__main__':
    unittest.main()
