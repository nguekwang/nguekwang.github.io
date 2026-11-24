"""Where the repository is: one place for every script in tools/.

Scripts import ROOT instead of working it out again from __file__
(.claude/rules/build-and-ci.md, readable-code.md in research-aide).
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
