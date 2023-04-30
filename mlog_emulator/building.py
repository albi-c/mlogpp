from enum import Enum


class BuildingType(Enum):
    CELL = "cell"
    MESSAGE = "message"


class Building:
    def __init__(self, type_: BuildingType, name: str, params: dict):
        self.type = type_
        self.name = name
        self.params = params
        self.state = {}

        if type_ == BuildingType.CELL:
            self.state["memory"] = [0 for _ in range(params["size"])]
        elif type_ == BuildingType.MESSAGE:
            self.state["text"] = ""
