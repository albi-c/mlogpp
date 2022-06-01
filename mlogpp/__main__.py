# from .lexer import Lexer
# from .preprocess import Preprocessor
# from .parser_ import Parser
# from .error import MlogError
# from .linker import Linker
# from .optimizer import Optimizer

# tokens = Lexer.lex(Preprocessor.preprocess("""
# print("Hello, World!")
# const _2a = (cell1[3] * a)
# cell1.enabled = cell1.x
# a = 1
# a += 2
# print(1 + _2a)
# if (1 > 2) {
#     print("1 > 2")
# } else {
#     for (i = 0; i < 10; i += 1) {
#         print(i)
#     }
# }
# printflush(message1)
# draw.color(255, 255, 255, 127)
# """))
# # print("\n".join(map(str, tokens)))
# ast = Parser().parse(tokens)
# try:
#     print(Linker.link([Optimizer.optimize(ast.generate())]))
# except MlogError as e:
#     e.print()
#     raise e

from . import cli
