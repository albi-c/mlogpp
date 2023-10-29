from .tokens import Token


class Preprocessor:
    """
    Executes macros.
    """

    @staticmethod
    def preprocess(code: list[Token]) -> list[Token]:
        return code
