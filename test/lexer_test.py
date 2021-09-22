import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from src.lexer import Token, TokenType, Lexer

def test_lexer():
    l = Lexer()
    t = l.lex("""\
functiona(@_1x,__2x){
print(1**2+3-4==1)
}""")
    assert t == [Token(TokenType.ID, "function"), Token(TokenType.ID, "a"), Token(TokenType.LPAREN, "("), Token(TokenType.ID, "@_1x"), Token(TokenType.COMMA, ","), Token(TokenType.ID, "__2x"), Token(TokenType.RPAREN, ")"), Token(TokenType.LBRACE, "{"), Token(TokenType.SEPARATOR, "\n"), Token(TokenType.ID, "print"), Token(TokenType.LPAREN, "("), Token(TokenType.NUMBER, "1"), Token(TokenType.OPERATOR, "**"), Token(TokenType.NUMBER, "2"), Token(TokenType.OPERATOR, "+"), Token(TokenType.NUMBER, "3"), Token(TokenType.OPERATOR, "-"), Token(TokenType.NUMBER, "4"), Token(TokenType.OPERATOR, "=="), Token(TokenType.NUMBER, "1"), Token(TokenType.RPAREN, ")")]
