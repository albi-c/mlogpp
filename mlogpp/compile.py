import os.path

from .lexer import Lexer
from .preprocess import Preprocessor
from .parser_rewrite import Parser
from .optimizer import Optimizer
from .linker import Linker


def compile_code(code: str, filename: str) -> str:
    code = Preprocessor.preprocess(code)
    code = Lexer(os.path.dirname(os.path.abspath(filename))).lex(code, filename)
    code = Parser().parse(code)
    code = code.generate()
    code = Linker.link(code)
    return code
