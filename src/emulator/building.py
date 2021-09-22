from enum import Enum

class EBuildingType(Enum):
    CELL    = "cell"
    MESSAGE = "message"

class EBuilding:
    def __init__(self, type_: EBuildingType, name: str, params: dict = None):
        self.type = type_
        self.name = name
        self.params = params if params is not None else {}
        self.state = {}

        if type_ == EBuildingType.CELL:
            self.state["memory"] = [0 for _ in range(params["size"])]
        elif type_ == EBuildingType.MESSAGE:
            self.state["text"] = ""
