# -*- coding: utf-8 -*-

"""
    add
    ~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_int

from pyasm import Program
from pyasm.instructions import push, mov, ret, pop, inc
from pyasm.registers import eax, esp, ebp

def test():
    prog = Program(
        push(ebp),
        mov(ebp, esp),
        mov(eax, ebp.addr+8),
        inc(eax),
        pop(ebp),
        ret(),
    )
    fun = prog.compile(c_int, [c_int])
    assert fun(1234) == 1235

if __name__ == '__main__':
    test()
