from .lexer import Lexer
from .preprocess import Preprocessor
from .parser_ import Parser

tokens = Lexer.lex(Preprocessor.preprocess("""
print.ab("Hello, World!")
const _2a = (cell1[1.5] * a)
a = 1
a += 2
print(1 + _2a)
for (i = 0; i < 10; i += 1) {
    print(i)
}
printflush(message1)
"""))
print("\n".join(map(repr, tokens)))
print(Parser().parse(tokens))

# from . import cli
