# import sys
# import os

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.join(os.path.dirname(SCRIPT_DIR), "mlog++"))

from lexer import Lexer
from parser_ import Parser
from generator import Generator

def test_generator():
    tokens = Lexer.preprocess(Lexer.lex("""
    const a = 10
    const b = 20
    print(10)
    print(a + b)
    if (a === b) {
        print(20)
    }
    printflush(message1)
"""))

    ast = Parser().parse(tokens)
    code = Generator().generate(ast)

    assert code == """\
print 10
print 30
jump 4 notEqual 0 true
print 20
printflush message1"""
