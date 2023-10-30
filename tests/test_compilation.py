import unittest

import os

from mlogpp.compile import compile_code

from mlog_emulator.vm import VM
from mlog_emulator.parser_ import Parser as VMParser
from mlog_emulator.building import Building, BuildingType


class CompilationTestCase(unittest.TestCase):
    CODE = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), os.path.join("examples", "test.mpp"))).read()

    def test_compilation(self):
        code = compile_code(CompilationTestCase.CODE, "<test>")

        vm = VM(*VMParser.parse(code))

        vm.env["variables"]["message1"] = Building(BuildingType.MESSAGE, "message1", {})

        vm.cycle()

        spl = vm["message1"].state["text"].split()
        self.assertIn(spl[0], ("1024", "1024.0"))
        self.assertIn(spl[1], ("10240", "10240.0"))
        self.assertEqual(spl[2], "-1")
        self.assertEqual(spl[3], "13")


if __name__ == '__main__':
    unittest.main()
