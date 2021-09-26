import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(SCRIPT_DIR), "mlog++"))

from lexer import Token, TokenType, Lexer

def test_lexer():
    t = Lexer.lex("""\
const a = test
function a(
# parameters
@_1x,__2x){
print(1**2+3-4==1)
}""")
    assert t[4].type == TokenType.ID and t[4].value == "function"
    assert t[7].type == TokenType.ID and t[7].value == "@_1x"

    t = Lexer.preprocess(t)

    print(Lexer.stringify_tokens(t))

    assert t[1].type == TokenType.ID and t[1].value == "test"
