class ABI:
    @staticmethod
    def function_name(name: str) -> str:
        return f"{name}()"

    @staticmethod
    def function_return(name: str) -> str:
        return f"__ret@{name}"

    @staticmethod
    def function_return_pos(name: str) -> str:
        return f"__ret_pos@{name}"

    @staticmethod
    def is_function(name: str) -> bool:
        return "()" in name

    @staticmethod
    def loop_name(name: str) -> str:
        return f"{name}$"

    @staticmethod
    def is_loop(name: str) -> bool:
        return "$" in name

    @staticmethod
    def loop_break(name: str) -> str:
        return f"__{name}_b"

    @staticmethod
    def loop_continue(name: str) -> str:
        return f"__{name}_c"

    @staticmethod
    def struct_field(struct: str, name: str) -> str:
        return f"{struct}::{name}"

    @staticmethod
    def struct_method(struct: str, name: str) -> str:
        return ABI.function_name(ABI.struct_field(struct, name))
