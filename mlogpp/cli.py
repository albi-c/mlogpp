import argparse, os, sys
from enum import Enum

import pyperclip

from .lexer import Lexer
from .preprocess import Preprocessor
from .parser_ import Parser
from .optimizer import Optimizer
from .linker import Linker
from .error import MlogError
from . import __version__

# input/output method
class IOMethod(Enum):
    FILE = 0
    STD  = 1
    CLIP = 2

parser = argparse.ArgumentParser(description="Mindustry logic compiler", prog="mlog++")

parser.add_argument("file", type=str, help="input file(s) [@clip for clipboard]", nargs="+")

parser.add_argument("-o:f", "--output-file", help="write output to a file")
parser.add_argument("-o:s", "--output-stdout", help="write output to stdout", action="store_true")
parser.add_argument("-o:c", "--output-clip", help="write output to clipboard (defualt)", action="store_true")

parser.add_argument("-v", "--verbose", help="print additional information", action="store_true")
parser.add_argument("-l", "--lines", help="print line numbers when output to stdout is selected", action="store_true")

parser.add_argument("-V", "--version", action="version", version=f"mlog++ {__version__}")

args = parser.parse_args()

omethod = IOMethod.CLIP
ofile = ""

verbose = False

# parse arguments
for k, v in vars(args).items():
    if v:
        if k.startswith("output"):
            # output method

            omethod = IOMethod.FILE if k.endswith("file") else IOMethod.STD if k.endswith("stdout") else IOMethod.CLIP
            if omethod == IOMethod.FILE:
                ofile = v
        
        elif k == "verbose":
            # verbose

            verbose = v

# check if files exist
for fn in args.file:
    # exists or is `@clip`
    if not os.path.isfile(fn) and fn != "@clip":
        print(f"Error: input file \"{fn}\" does not exist")
        sys.exit(1)

# read files
datas = []
for fn in args.file:
    if fn == "@clip":
        # clipboard

        datas.append((fn, pyperclip.paste()))

    else:
        # file

        with open(fn, "r") as f:
            datas.append((fn, f.read()))

# compile all files
outs = []
for data in datas:
    # skip if already compiler
    if data[0].endswith(".mind") or data[0].endswith(".masm"):
        outs.append(data[1])
        continue
    
    try:
        out = Preprocessor.preprocess(data[1])
        out = Lexer.lex(out)
        out = Parser().parse(out)
        out = out.generate()
        out = Optimizer.optimize(out)
    except MlogError as e:
        e.print()
        raise e
        sys.exit(1)

    # add to compiled files
    outs.append(out)

# link the compiled files
out = Linker.link(outs).strip()

if omethod == IOMethod.FILE:
    # output to file

    with open(ofile, "w+") as f:
        f.write(out)

elif omethod == IOMethod.STD:
    # output to stdout

    # check if line numbers should be prined
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
    # output to clipboard

    pyperclip.copy(out)

if verbose:
    print(f"Output: {len(out.strip())} characters, {len(out.strip().split())} words, {len(out.strip().splitlines())} lines")
