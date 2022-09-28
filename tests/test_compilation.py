import unittest

from mlogpp.lexer import Lexer
from mlogpp.preprocess import Preprocessor
from mlogpp.parser_ import Parser
from mlogpp.optimizer import Optimizer
from mlogpp.linker import Linker

from mlog_emulator.vm import VM
from mlog_emulator.parser_ import Parser as VMParser


class CompilationTestCase(unittest.TestCase):
    CODE = """\
const LOOP_UNTIL = 5

x = 10

function func1(x, y) {
    x = 12
    y = 20
    return x + y
}
 
function func2(n) {
    global x
    
    x = n ** 2
}

val = func1(3, 4)
func2(val)

y = 0
for (i : LOOP_UNTIL) {
    y += i * x
}"""

    def test_compilation(self):
        code = Preprocessor.preprocess(CompilationTestCase.CODE)
        code = Lexer("TEST_CODE_DIR").lex(code, "TEST_CODE_FILE")
        code = Parser().parse(code)
        code = code.generate()
        code = Optimizer.optimize(code)
        code = Linker.link([code])

        vm = VM(*VMParser.parse(code))

        vm.cycle()

        self.assertEqual(vm["x"], 1024)
        self.assertEqual(vm["y"], 10240)


if __name__ == '__main__':
    unittest.main()
