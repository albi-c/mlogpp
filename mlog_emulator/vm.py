from .parser_ import Instruction

class VMSignal(Exception):
    pass

class VM:
    def __init__(self, ins: list):
        self.ins = ins
        self.env = {
            "variables": {
                "_": 0,
                "null": None,
                "true": True,
                "false": False,

                # Special variables
                "@this": None,
                "@thisx": 0,
                "@thisy": 0,
                "@ipt": 0,
                "@counter": 0,
                "@links": 0,
                "@unit": None,
                "@time": 0,
                "@tick": 0,
                "@mapw": 0,
                "@maph": 0
            },

            "print_buffer": ""
        }
    
    def next_ins(self) -> Instruction:
        if self.env["variables"]["@counter"] < len(self.ins) - 1:
            return self.ins[self.env["variables"]["@counter"]]
        
        raise VMSignal()
    
    def step(self) -> bool:
        try:
            i = self.next_ins()
        except VMSignal:
            return False
        
        self.env["variables"]["@counter"] += 1
        i.execute(self.env)
        
        return True
    
    def cycle(self) -> dict:
        while self.step():
            pass

        return self.env
