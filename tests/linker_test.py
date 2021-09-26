import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(SCRIPT_DIR), "mlog++"))

from linker import Linker

def test_linker():
    code = Linker.link(["""
wait 0.1""",
"""
print 10
printflush message1
jump 0 always _ _"""])

    assert code == """\
wait 0.1
print 10
printflush message1
jump 1 always _ _"""
