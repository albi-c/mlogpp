import unittest

from mlogpp.compile import compile_code

from mlog_emulator.vm import VM
from mlog_emulator.parser_ import Parser as VMParser
from mlog_emulator.building import Building, BuildingType


class CompilationTestCase(unittest.TestCase):
    CODE = """\
const LOOP_UNTIL = 5

let x = 10

function func1(num x, num y) -> num {
    x = 12
    y = 20
    return x + y
}

function func2(num n) {
    x = n ** 2
}

num val = func1(3, 4)
func2(val)

num y = 0
for (i : LOOP_UNTIL) {
    y += i * x
}

struct Vec2 {
    num x, y
}

function vec2_add(Vec2 a, Vec2 b) -> Vec2 {
    return Vec2(a.x + b.x, a.y + b.y)
}

let v1 = Vec2(-3.5, 6)
let v2 = Vec2(2.5, 7)
let v = vec2_add(v1, v2)

Block message1
print(x)
print(" ")
print(y)
print(" ")
print(v.x)
print(" ")
print(v.y)
printflush(message1)
"""

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
