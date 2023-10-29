import os.path

from .generator import Gen
from .preprocess import Preprocessor
from .lexer import Lexer
from .parser import Parser
from .optimizer import Optimizer
from .linker import Linker
from .scope import Scope
from .value_types import Type
from .builtins import BUILTINS
from .asm.parser import AsmParser


def compile_code(code: str, filename: str) -> str:
    """
    Compile mlog++ code

    Args:
        code: The code to be compiled.
        filename: Name of the compiled file. Used for imports and errors.

    Returns:
        The compiled code.
    """

    Gen.reset()
    Scope.reset(BUILTINS)
    Type.reset()

    code = Lexer(os.path.dirname(os.path.abspath(filename))).lex(code, filename)
    code = Preprocessor.preprocess(code)
    code = Parser().parse(code)
    code.gen()
    code = Gen.get()
    code = Optimizer.optimize(code)
    code = Scope.get_config() + code
    code = Linker.link(code)

    return code


def compile_asm(code: str, filename: str) -> str:
    """
    Compile mlog++ assembly code

    Args:
        code: The code to be compiled.
        filename: Name of the compiled file. Used for imports and errors.

    Returns:
        The compiled code.
    """

    # reset the state
    Gen.reset()
    Scope.reset(BUILTINS)
    Type.reset()

    code = Lexer(os.path.dirname(os.path.abspath(filename))).lex(code, filename)
    code = Preprocessor.preprocess(code)
    code = AsmParser().parse(code)
    code.gen()
    code = Gen.get()
    code = Linker.link(code)

    return str(code)
