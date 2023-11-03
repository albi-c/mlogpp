import unittest

import os

from mlogpp.compile import compile_code

from mlog_emulator.vm import VM
from mlog_emulator.parser_ import Parser as VMParser
from mlog_emulator.building import Building, BuildingType


class CompilationTestCase(unittest.TestCase):
    DATA: list[tuple[str, str]] = [
        ("test.mpp", "1024 10240 -1 13"),
        ("struct.mpp", "15 20 | 25 35 | 1 2 3 4 | 5, 6 | 7, 6, 7 | 7, 6 | " + ("a" * 10)),
        ("range.mpp", "2 3 4 5"),
        ("const.mpp", "501012"),
        ("const_expression.mpp", "58811358"),
        ("imports.mpp", "30"),
        ("inline_asm.mpp", "47 -10" + "".join(f"{i+1}\\n5XXXXX2.5" for i in range(10))),
        ("scopes.mpp", "0 10")
    ]

    def _test_compilation(self, name: str, output: str):
        with self.subTest(name):
            filename = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.path.join("examples", name))
            with open(filename) as f:
                code = f.read()

            code = compile_code(code, filename)

            vm = VM(*VMParser.parse(code))

            vm.env["variables"]["message1"] = Building(BuildingType.MESSAGE, "message1", {})
            for i in range(10):
                vm.env["variables"][f"cell{i}"] = Building(BuildingType.CELL, "cell1", {"size": 64})

            vm.cycle()

            self.assertEqual(vm["message1"].state["text"].strip().replace(".0", ""), output)

    def test_compilation(self):
        for name, output in CompilationTestCase.DATA:
            self._test_compilation(name, output)


if __name__ == '__main__':
    unittest.main()
