import unittest
import os

from mlogpp.compile import compile_code, compile_asm


class ExamplesTestCase(unittest.TestCase):
    def test_examples_compilation(self):
        directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
        examples = [os.path.join(directory, fn) for fn in os.listdir(directory) if fn.endswith(".mpp")]
        for filename in examples:
            with self.subTest(msg=filename):
                with open(filename, "r") as f:
                    code = f.read()

                compile_code(code, filename)

    def test_asm_examples_compilation(self):
        directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
        examples = [os.path.join(directory, fn) for fn in os.listdir(directory) if fn.endswith(".ma")]
        for filename in examples:
            with self.subTest(msg=filename):
                with open(filename, "r") as f:
                    code = f.read()

                compile_asm(code, filename)


if __name__ == '__main__':
    unittest.main()
