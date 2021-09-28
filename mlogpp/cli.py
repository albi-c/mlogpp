import argparse, os, sys
from enum import Enum

import pyperclip

from .lexer import Lexer
from .parser_ import Parser
from .generator import Generator
from .linker import Linker

class IOMethod(Enum):
    FILE = 0
    STD  = 1
    CLIP = 2

parser = argparse.ArgumentParser(description="Mindustry logic compiler", prog="mlog++")

parser.add_argument("file", type=str, help="input file(s)", nargs="+")

parser.add_argument("-o:f", "--output-file", help="write output to a file")
parser.add_argument("-o:s", "--output-stdout", help="write output to stdout", action="store_true")
parser.add_argument("-o:c", "--output-clip", help="write output to clipboard (defualt)", action="store_true")

parser.add_argument("-O0", "--optimize0", help="disable optimization (WARNING: creates extremely unoptimized code)", action="store_true")
parser.add_argument("-O1", "--optimize1", help="set optimization level to 1", action="store_true")
parser.add_argument("-O2", "--optimize2", help="set optimization level to 2", action="store_true")

parser.add_argument("-v", "--verbose", help="print additional information", action="store_true")
parser.add_argument("-l", "--lines", help="print line numbers when output to stdout is selected", action="store_true")

parser.add_argument("-V", "--version", action="version", version="mlog++ 1.3")

args = parser.parse_args()

omethod = IOMethod.CLIP
ofile = ""

optlevel = 2

verbose = False

for k, v in vars(args).items():
    if v:
        if k.startswith("output"):
            omethod = IOMethod.FILE if k.endswith("file") else IOMethod.STD if k.endswith("stdout") else IOMethod.CLIP
            if omethod == IOMethod.FILE:
                ofile = v
        elif k.startswith("optimize"):
            optlevel = int(k[-1])
        elif k == "verbose":
            verbose = v

for fn in args.file:
    if not os.path.isfile(fn):
        print(f"Error: input file \"{fn}\" does not exist")
        sys.exit(1)

datas = []
for fn in args.file:
    with open(fn, "r") as f:
        datas.append((fn, f.read()))

optimization_levels = {
    0: {"enable": False},
    1: {"unused": False},
    2: {}
}

outs = []
for data in datas:
    if data[0].endswith(".mind"):
        outs.append(data[1])
        continue

    out = Lexer.preprocess(Lexer.lex(Lexer.resolve_includes(data[1])))
    out = Parser().parse(out)
    out = Generator().generate(out, optimization_levels[optlevel])
    outs.append(out)

if len(outs) > 1:
    out = Linker.link(outs).strip()
else:
    out = outs[0].strip()

if omethod == IOMethod.FILE:
    with open(ofile, "w+") as f:
        f.write(out)
elif omethod == IOMethod.STD:
    if vars(args)["lines"]:
        lines = out.splitlines()
        maxline = len(str(len(lines)))
        for i, ln in enumerate(lines):
            print(f"{str(i).zfill(maxline)}: {ln}")
    else:
        print(out)
    
    if verbose:
        print()
elif omethod == IOMethod.CLIP:
    pyperclip.copy(out)

if verbose:
    print(f"Output: {len(out.strip())} characters, {len(out.strip().split())} words, {len(out.strip().splitlines())} lines")
