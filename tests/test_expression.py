import unittest

from mlogpp.expression import Expression
from mlogpp.util import Position


class ExpressionTestCase(unittest.TestCase):
    def test_expression(self):
        pos = Position(0, 0, 0, "<test>", "<test>")
        self.assertEqual(Expression.exec(pos, 'n=3\n"a"*(10//n+2)'), [3, "aaaaa"])
        self.assertEqual(Expression.exec(pos, '"a" if 2 > 3 else "b"'), ["b"])


if __name__ == '__main__':
    unittest.main()
