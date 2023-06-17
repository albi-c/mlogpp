import os.path

from .generator import Gen
from .preprocess import Preprocessor
from .lexer import Lexer
from .parser import Parser
from .linker import Linker
from .scope import Scope


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
    Scope.reset()

    code = Preprocessor.preprocess(code)
    code = Lexer(os.path.dirname(os.path.abspath(filename))).lex(code, filename)
    code = Parser().parse(code)
    code.gen()
    code = Gen.get()
    # TODO: optimize
    code = Linker.link(code)

    return code


# def compile_asm(code: str, filename: str) -> str:
#     """
#     Compile mlog++ assembly code
#
#     Args:
#         code: The code to be compiled.
#         filename: Name of the compiled file. Used for imports and errors.
#
#     Returns:
#         The compiled code.
#     """
#
#     # reset the state
#     Scopes.reset()
#     Gen.reset()
#
#     code = Preprocessor.preprocess(code)
#     code = Lexer(os.path.dirname(os.path.abspath(filename))).lex(code, filename)
#     code = AsmParser().parse(code)
#     code = code.generate()
#     code = Linker.link(code)
#
#     return str(code)
