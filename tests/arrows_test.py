import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(SCRIPT_DIR), "mlog++"))

import arrows

def test_arrows():
    assert arrows.generate(4, 1) == "    ^"
    assert arrows.generate(0, 5) == "^^^^^"
