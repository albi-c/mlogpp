from .instruction import Instruction


class Gen:
    _instructions: list[Instruction] = []
    _tmp_index = 0

    def __init__(self):
        raise TypeError(f"{self.__module__}.{self.__class__.__name__} cannot be constructed")

    @classmethod
    def reset(cls):
        cls._instructions = []

    @classmethod
    def emit(cls, *ins: Instruction):
        cls._instructions += ins

    @classmethod
    def get(cls) -> list[Instruction]:
        return cls._instructions

    @classmethod
    def tmp(cls) -> str:
        cls._tmp_index += 1
        return f"__tmp{cls._tmp_index}"


Gen.reset()
