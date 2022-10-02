import os.path

from .scope import Scopes
from .generator import Gen

from .preprocess import Preprocessor
from .lexer import Lexer
from .parser_ import Parser
from .optimizer import Optimizer
from .linker import Linker


def compile_code(code: str, filename: str) -> str:
    Scopes.reset()
    Gen.reset()

    code = Preprocessor.preprocess(code)
    code = Lexer(os.path.dirname(os.path.abspath(filename))).lex(code, filename)
    code = Parser().parse(code)
    code = code.generate()
    code = Optimizer.optimize(code)
    code = Linker.link(code)

    return code
