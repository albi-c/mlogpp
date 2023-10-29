import unittest

from mlogpp.lexer import *


class LexerTestCase(unittest.TestCase):
    SOURCE_CODE = """\
# testing source code

num x = 23
num a = x + 1
x += 80

cell1[10] = 2
cell1[10] += cell1[4]

function func(num a, num b) -> num {
    return a + x
}

ucontrol.move(x, x + 1)

str message = "Hello!"
UnitType unit = @zenith

print(message)
print(unit)

if (unit == @surge-alloy) {
    num s = true
} else {
    num s = false
}

while (true) {
    a += 1
    if (a > x) {
        break
    }
}

for (num i = 1; i <= 10; i += 1) {
    print(i)
    if (i == 5) {
        continue
    }
}

ubind(@mega)
"""

    TOKENS = (
        (TokenType.ID, "num"),
        (TokenType.ID, "x"),
        (TokenType.SET, "="),
        (TokenType.NUMBER, "23"),
        (TokenType.ID, "num"),
        (TokenType.ID, "a"),
        (TokenType.SET, "="),
        (TokenType.ID, "x"),
        (TokenType.OPERATOR, "+"),
        (TokenType.NUMBER, "1"),
        (TokenType.ID, "x"),
        (TokenType.SET, "+="),
        (TokenType.NUMBER, "80"),
        (TokenType.ID, "cell1"),
        (TokenType.LBRACK, "["),
        (TokenType.NUMBER, "10"),
        (TokenType.RBRACK, "]"),
        (TokenType.SET, "="),
        (TokenType.NUMBER, "2"),
        (TokenType.ID, "cell1"),
        (TokenType.LBRACK, "["),
        (TokenType.NUMBER, "10"),
        (TokenType.RBRACK, "]"),
        (TokenType.SET, "+="),
        (TokenType.ID, "cell1"),
        (TokenType.LBRACK, "["),
        (TokenType.NUMBER, "4"),
        (TokenType.RBRACK, "]"),
        (TokenType.KEYWORD, "function"),
        (TokenType.ID, "func"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "num"),
        (TokenType.ID, "a"),
        (TokenType.COMMA, ","),
        (TokenType.ID, "num"),
        (TokenType.ID, "b"),
        (TokenType.RPAREN, ")"),
        (TokenType.ARROW, "->"),
        (TokenType.ID, "num"),
        (TokenType.LBRACE, "{"),
        (TokenType.KEYWORD, "return"),
        (TokenType.ID, "a"),
        (TokenType.OPERATOR, "+"),
        (TokenType.ID, "x"),
        (TokenType.RBRACE, "}"),
        (TokenType.ID, "ucontrol"),
        (TokenType.OPERATOR, "."),
        (TokenType.ID, "move"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "x"),
        (TokenType.COMMA, ","),
        (TokenType.ID, "x"),
        (TokenType.OPERATOR, "+"),
        (TokenType.NUMBER, "1"),
        (TokenType.RPAREN, ")"),
        (TokenType.ID, "str"),
        (TokenType.ID, "message"),
        (TokenType.SET, "="),
        (TokenType.STRING, "\"Hello!\""),
        (TokenType.ID, "UnitType"),
        (TokenType.ID, "unit"),
        (TokenType.SET, "="),
        (TokenType.ID, "@zenith"),
        (TokenType.ID, "print"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "message"),
        (TokenType.RPAREN, ")"),
        (TokenType.ID, "print"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "unit"),
        (TokenType.RPAREN, ")"),
        (TokenType.KEYWORD, "if"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "unit"),
        (TokenType.OPERATOR, "=="),
        (TokenType.ID, "@surge-alloy"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "num"),
        (TokenType.ID, "s"),
        (TokenType.SET, "="),
        (TokenType.ID, "true"),
        (TokenType.RBRACE, "}"),
        (TokenType.KEYWORD, "else"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "num"),
        (TokenType.ID, "s"),
        (TokenType.SET, "="),
        (TokenType.ID, "false"),
        (TokenType.RBRACE, "}"),
        (TokenType.KEYWORD, "while"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "true"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "a"),
        (TokenType.SET, "+="),
        (TokenType.NUMBER, "1"),
        (TokenType.KEYWORD, "if"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "a"),
        (TokenType.OPERATOR, ">"),
        (TokenType.ID, "x"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.KEYWORD, "break"),
        (TokenType.RBRACE, "}"),
        (TokenType.RBRACE, "}"),
        (TokenType.KEYWORD, "for"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "num"),
        (TokenType.ID, "i"),
        (TokenType.SET, "="),
        (TokenType.NUMBER, "1"),
        (TokenType.SEMICOLON, ";"),
        (TokenType.ID, "i"),
        (TokenType.OPERATOR, "<="),
        (TokenType.NUMBER, "10"),
        (TokenType.SEMICOLON, ";"),
        (TokenType.ID, "i"),
        (TokenType.SET, "+="),
        (TokenType.NUMBER, "1"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "print"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "i"),
        (TokenType.RPAREN, ")"),
        (TokenType.KEYWORD, "if"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "i"),
        (TokenType.OPERATOR, "=="),
        (TokenType.NUMBER, "5"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.KEYWORD, "continue"),
        (TokenType.RBRACE, "}"),
        (TokenType.RBRACE, "}"),
        (TokenType.ID, "ubind"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "@mega"),
        (TokenType.RPAREN, ")")
    )

    def test_lexer(self):
        tokens = Lexer("TEST_CODE_DIR").lex(LexerTestCase.SOURCE_CODE, "TEST_CODE_FILE")
        token_tuples = tuple(map(lambda t: (t.type, t.value), tokens))
        self.assertEqual(token_tuples, LexerTestCase.TOKENS)


if __name__ == '__main__':
    unittest.main()
