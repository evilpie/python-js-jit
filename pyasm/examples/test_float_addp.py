# -*- coding: utf-8 -*-

"""
    float_sub
    ~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_float

from pyasm import Program
from pyasm.instructions import push, mov, ret, pop, fld, faddp
from pyasm.registers import esp, ebp

def test():
    prog = Program(
        push(ebp),
        mov(ebp, esp),
        fld(ebp.addr+8),
        fld(ebp.addr+12),
        faddp(),
        pop(ebp),
        ret(),
    )
    fun = prog.compile(c_float, [c_float, c_float])
    assert fun(4, 2) == 6.0

if __name__ == '__main__':
    test()
