from parser_ import EInstruction

class EVMSignal(Exception):
    pass

class EVM:
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
    
    def next_ins(self) -> EInstruction:
        if self.env["variables"]["@counter"] < len(self.ins) - 1:
            return self.ins[self.env["variables"]["@counter"]]
        
        raise EVMSignal()
    
    def run(self) -> dict:
        while True:
            try:
                i = self.next_ins()
            except EVMSignal:
                break
            
            self.env["variables"]["@counter"] += 1

            i.execute(self.env)

        return self.env
