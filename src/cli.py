import argparse, os, sys
from enum import Enum

import pyperclip

from preprocessor import Preprocessor
from lexer import Lexer
from parser_ import Parser
from generator import Generator

class IOMethod(Enum):
    FILE = 0
    STD  = 1
    CLIP = 2

parser = argparse.ArgumentParser(description="Mindustry logic compiler")

parser.add_argument("file", type=str, help="input file to compile")

parser.add_argument("-o:f", "--output-file", help="write output to a file")
parser.add_argument("-o:s", "--output-stdout", help="write output to stdout", action="store_true")
parser.add_argument("-o:c", "--output-clip", help="write output to clipboard (defualt)", action="store_true")

parser.add_argument("-O0", "--optimize0", help="disable optimization (WARNING: creates extremely unoptimized code)", action="store_true")
parser.add_argument("-O1", "--optimize1", help="set optimization level to 1", action="store_true")
parser.add_argument("-O2", "--optimize2", help="set optimization level to 2", action="store_true")

args = parser.parse_args()

omethod = IOMethod.CLIP
ofile = ""

optlevel = 2

for k, v in vars(args).items():
    if v:
        if k.startswith("output"):
            omethod = IOMethod.FILE if k.endswith("file") else IOMethod.STD if k.endswith("stdout") else IOMethod.CLIP
            if omethod == IOMethod.FILE:
                ofile = v
        elif k.startswith("optimize"):
            optlevel = int(k[-1])

if not os.path.isfile(args.file):
    print("Error: input file does not exist")
    sys.exit(1)

with open(args.file, "r") as f:
    data = f.read()

optimization_levels = {
    0: {"enable": False},
    1: {"unused": False},
    2: {}
}

out = Preprocessor().preprocess(data)
out = Lexer().lex(out)
out = Parser().parse(out)
out = Generator().generate(out, optimization_levels[optlevel])

if omethod == IOMethod.FILE:
    with open(ofile, "w+") as f:
        f.write(out)
elif omethod == IOMethod.STD:
    print(out)
elif omethod == IOMethod.CLIP:
    pyperclip.copy(out)
