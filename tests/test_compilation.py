import unittest

from mlogpp.compile import compile_code

from mlog_emulator.vm import VM
from mlog_emulator.parser_ import Parser as VMParser


class CompilationTestCase(unittest.TestCase):
    CODE = """\
const LOOP_UNTIL = 5

num x = 10

function func1(num x, num y) -> num {
    x = 12
    y = 20
    return x + y
}

x = func1(3, 4)
x **= 2

num y = 0
for (i : LOOP_UNTIL) {
    y += i * x
}"""

    def test_compilation(self):
        code = compile_code(CompilationTestCase.CODE, "")

        vm = VM(*VMParser.parse(code))

        vm.cycle()

        self.assertEqual(vm["x"], 1024)
        self.assertEqual(vm["y"], 10240)


if __name__ == '__main__':
    unittest.main()
