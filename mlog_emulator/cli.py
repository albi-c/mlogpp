import argparse
import os
import sys

import pyperclip

from .parser_ import Parser
from .vm import VM


def main():
    parser = argparse.ArgumentParser(description="Mindustry logic mlog_emulator", prog="mlog++/mlog_emulator")

    parser.add_argument("file", type=str, help="input file [@clip for clipboard]")

    args = parser.parse_args()

    fn = args.file
    if fn == "@clip":
        code = pyperclip.paste()
    else:
        if not os.path.isfile(fn):
            print(f"Error: input file \"{fn}\" does not exist")
            sys.exit(1)

        with open(fn, "r") as f:
            code = f.read()

    VM(*Parser.parse(code))
