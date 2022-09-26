import unittest

from mlogpp.linker import *


class GeneratorTestCase(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(Linker.link([
            """\
print 0
<lab1
print 1
>lab1
print 2"""
        ]), """\
print 0
print 1
jump 1 always _ _
print 2""")

    def test_joining(self):
        self.assertEqual(Linker.link([
            """\
print 0
<lab1
print 1
>lab1
""",
            """\
print 2
<lab2
print 3
>lab1
>lab2
print 4"""
        ]), """\
print 0
print 1
jump 1 always _ _
print 2
print 3
jump 1 always _ _
jump 4 always _ _
print 4""")


if __name__ == '__main__':
    unittest.main()
