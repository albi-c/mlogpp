import unittest

from mlogpp.lexer import *


class LexerTestCase(unittest.TestCase):
    SOURCE_CODE = """\
# testing source code

x = 23
a = x + 1
x += 80

cell1[10] = 2
cell1[10] += cell1[4]

function func(a, b) {
    global a, x
    return a + x
}

ucontrol.move(x, x + 1)

unit = @zenith

print(unit)

if (unit == @surge-alloy) {
    s = true
} else {
    s = false
}

while (true) {
    a += 1
    if (a > x) {
        break
    }
}

for (i = 1; i <= 10; i += 1) {
    print(i)
    if (i == 5) {
        continue
    }
}

ubind(@mega)
"""

    TOKENS = (
        (TokenType.ID, "x"),
        (TokenType.SET, "="),
        (TokenType.NUMBER, "23"),
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
        (TokenType.ID, "function"),
        (TokenType.ID, "func"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "a"),
        (TokenType.COMMA, ","),
        (TokenType.ID, "b"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "global"),
        (TokenType.ID, "a"),
        (TokenType.COMMA, ","),
        (TokenType.ID, "x"),
        (TokenType.ID, "return"),
        (TokenType.ID, "a"),
        (TokenType.OPERATOR, "+"),
        (TokenType.ID, "x"),
        (TokenType.RBRACE, "}"),
        (TokenType.ID, "ucontrol.move"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "x"),
        (TokenType.COMMA, ","),
        (TokenType.ID, "x"),
        (TokenType.OPERATOR, "+"),
        (TokenType.NUMBER, "1"),
        (TokenType.RPAREN, ")"),
        (TokenType.ID, "unit"),
        (TokenType.SET, "="),
        (TokenType.ID, "@zenith"),
        (TokenType.ID, "print"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "unit"),
        (TokenType.RPAREN, ")"),
        (TokenType.ID, "if"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "unit"),
        (TokenType.OPERATOR, "=="),
        (TokenType.ID, "@surge-alloy"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "s"),
        (TokenType.SET, "="),
        (TokenType.ID, "true"),
        (TokenType.RBRACE, "}"),
        (TokenType.ID, "else"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "s"),
        (TokenType.SET, "="),
        (TokenType.ID, "false"),
        (TokenType.RBRACE, "}"),
        (TokenType.ID, "while"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "true"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "a"),
        (TokenType.SET, "+="),
        (TokenType.NUMBER, "1"),
        (TokenType.ID, "if"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "a"),
        (TokenType.OPERATOR, ">"),
        (TokenType.ID, "x"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "break"),
        (TokenType.RBRACE, "}"),
        (TokenType.RBRACE, "}"),
        (TokenType.ID, "for"),
        (TokenType.LPAREN, "("),
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
        (TokenType.ID, "if"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "i"),
        (TokenType.OPERATOR, "=="),
        (TokenType.NUMBER, "5"),
        (TokenType.RPAREN, ")"),
        (TokenType.LBRACE, "{"),
        (TokenType.ID, "continue"),
        (TokenType.RBRACE, "}"),
        (TokenType.RBRACE, "}"),
        (TokenType.ID, "ubind"),
        (TokenType.LPAREN, "("),
        (TokenType.ID, "@mega"),
        (TokenType.RPAREN, ")"),
    )

    def test_lex(self):
        tokens = Lexer.lex(LexerTestCase.SOURCE_CODE)
        token_tuples = tuple(map(lambda t: (t.type, t.value), tokens))
        self.assertEqual(token_tuples, LexerTestCase.TOKENS)

    def test_match(self):
        self.assertEqual(Lexer.match("@surge-alloy.property"), TokenType.ID)
        self.assertEqual(Lexer.match("\"Hello, World!\""), TokenType.STRING)
        self.assertEqual(Lexer.match("437689"), TokenType.NUMBER)
        self.assertEqual(Lexer.match("12.569"), TokenType.NUMBER)
        self.assertEqual(Lexer.match("("), TokenType.LPAREN)
        self.assertEqual(Lexer.match(")"), TokenType.RPAREN)
        self.assertEqual(Lexer.match("{"), TokenType.LBRACE)
        self.assertEqual(Lexer.match("}"), TokenType.RBRACE)
        self.assertEqual(Lexer.match("["), TokenType.LBRACK)
        self.assertEqual(Lexer.match("]"), TokenType.RBRACK)
        self.assertEqual(Lexer.match(","), TokenType.COMMA)
        self.assertEqual(Lexer.match(";"), TokenType.SEMICOLON)
        self.assertEqual(Lexer.match(":"), TokenType.COLON)

        operator_tokens = ("+", "-", "*", "/", "!", "**", "===", "<=", ">=", "==", "!=", "<", ">", "~")
        self.assertEqual(
            tuple(map(Lexer.match, operator_tokens)),
            (TokenType.OPERATOR,) * len(operator_tokens)
        )

        set_tokens = ("=", "+=", "-=", "*=", "+=")
        self.assertEqual(
            tuple(map(Lexer.match, set_tokens)),
            (TokenType.SET,) * len(set_tokens)
        )

        self.assertEqual(Lexer.match("&&"), TokenType.LOGIC)
        self.assertEqual(Lexer.match("||"), TokenType.LOGIC)

        none_tokens = (
            "\"Hello, World!",
            "#500",
            "12value"
        )
        self.assertEqual(
            tuple(map(Lexer.match, none_tokens)),
            (TokenType.NONE,) * len(none_tokens)
        )


if __name__ == '__main__':
    unittest.main()
