# -*- coding: utf-8 -*-

"""
    add
    ~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_int

from pyasm import Program
from pyasm.instructions import mov, ret, lea
from pyasm.registers import eax, ebx

def test():
    prog = Program(
        mov(ebx, 10),
        lea(eax, ebx, 20),
        ret(),
    )
    fun = prog.compile(c_int)
    assert fun() == 30

if __name__ == '__main__':
    test()
