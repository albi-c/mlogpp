import os.path

from .scope import Scopes
from .generator import Gen

from .preprocess import Preprocessor
from .lexer import Lexer
from .parser_ import Parser
from .optimizer import Optimizer
from .linker import Linker


def compile_code(code: str, filename: str) -> str:
    """
    Compile mlog++ code

    Args:
        code: The code to be compiled.
        filename: Name of the compiled file. Used for imports and errors.

    Returns:
        The compiled code.
    """

    # reset the state
    Scopes.reset()
    Gen.reset()

    code = Preprocessor.preprocess(code)
    code = Lexer(os.path.dirname(os.path.abspath(filename))).lex(code, filename)
    code = Parser().parse(code)
    code = code.generate()
    code = Optimizer.optimize(code)
    code = Linker.link(code)

    return code
