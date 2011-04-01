# -*- coding: utf-8 -*-

"""
    echo
    ~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_long

from pyasm import Program
from pyasm.instructions import mov, ret
from pyasm.registers import rax, rdi

if __name__ == '__main__':
    #linux only call convention, not valid for windows
    prog = Program(
        mov(rax, rdi),
        ret(),
    )
    fun = prog.compile(restype=c_long)
    assert fun(1234) == 1234
