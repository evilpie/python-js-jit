# -*- coding: utf-8 -*-

"""
    pyasm.__init__
    ~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

import sys
from pyasm.exceptions import AssemblyError
from pyasm.base import Instruction, Label
from pyasm.program import Program, Executable, compile

if sys.maxint == 0x7fffffffffffffff:
    target = 'x86-64'
elif sys.maxint == 0x7fffffff:
    target = 'x86'
