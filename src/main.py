from preprocessor import Preprocessor
from lexer import Lexer
from parser_ import Parser
from generator import Generator

test_code1 = """
function add_print(a, b) {
    print(a + b)
}
x = 0
y = 12
while (x < y) {
    add_print(x, 1)
    if (x < (y - 1)) {
        print(", ")
    }
    x += 1
}
if (y >= 10 || x == -1) {
    print("\\nY is larger than 10!\\n")
}
for (i = 0; i < 5; i += 1) {
    print(i + " ")
}
printflush()
"""

test_code2 = """
const CRYO_THRESHOLD = 10

for (i = 0; i < @links; i += 1) {
    .getlink reactor i
    .sensor cryo reactor @cryofluid
    control(enabled, reactor, cryo >= CRYO_THRESHOLD, 0, 0, 0)
}
"""

test_code3 = """
x = -10
if (x != 10) {
    print(10)
    print(read(y, cell1, 10))
    print(getlink(z, 2))
    #print(y)
}
print(20)
"""

p = Preprocessor()
c = p.preprocess(test_code3)

l = Lexer()
r = l.lex(c)

p = Parser()
a = p.parse(r)

g = Generator()
m = g.generate(a)

for i, ln in enumerate(m.splitlines()):
    print(f"{i}: {ln}")
