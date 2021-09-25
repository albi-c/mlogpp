from parser_ import EParser
from vm import EVM
from building import EBuilding, EBuildingType

class Emulator:
    def __init__(self, code: str, buildings: list = None):
        self.code = code
        self.ins = EParser().parse(code)
        self.buildings = buildings if buildings is not None else []
    
    def run(self) -> dict:
        vm = EVM(self.ins)
        for b in self.buildings:
            vm.env["variables"][b.name] = b

        return vm.run()

if __name__ == "__main__":
    buildings = [
        EBuilding(EBuildingType.MESSAGE, "message1")
    ]

    e = Emulator("""
set x 10
op add x x 10
print x
printflush message1
end
""", buildings)

    env = e.run()

    for b in buildings:
        print(b.state)
