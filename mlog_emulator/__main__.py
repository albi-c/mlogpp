import argparse, os, sys

import pyperclip

from .vm import VM
from .parser_ import Parser, Instruction
from .building import Building, BuildingType

parser = argparse.ArgumentParser(description="Mindustry logic mlog_emulator", prog="mlog++/mlog_emulator")

parser.add_argument("file", type=str, help="input file [@clip for clipboard]")

args = parser.parse_args()

fn = args.file
code = ""
if fn == "@clip":
    code = pyperclip.paste()
else:
    if not os.path.isfile(fn):
        print(f"Error: input file \"{fn}\" does not exist")
        sys.exit(1)
    
    with open(fn, "r") as f:
        code = f.read()

vm = VM(Parser.parse(code))

