import unittest
import os

from mlogpp.lexer import Lexer
from mlogpp.preprocess import Preprocessor
from mlogpp.parser_ import Parser
from mlogpp.optimizer import Optimizer
from mlogpp.linker import Linker


class ExamplesTestCase(unittest.TestCase):
    def test_examples_compilation(self):
        directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
        examples = [os.path.join(directory, fn) for fn in os.listdir(directory) if fn.endswith(".mpp")]
        for filename in examples:
            with self.subTest(msg=filename):
                with open(filename, "r") as f:
                    code = f.read()

                code = Preprocessor.preprocess(code)
                code = Lexer.lex(code, filename, directory)
                code = Parser().parse(code)
                code = code.generate()
                code = Optimizer.optimize(code)
                code = Linker.link([code])


if __name__ == '__main__':
    unittest.main()
