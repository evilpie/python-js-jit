# -*- coding: utf-8 -*-

"""
    loop
    ~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_int

from pyasm import Program, Label
from pyasm.instructions import mov, ret, inc, jl, cmp
from pyasm.registers import eax

def test():
    label = Label('foo')
    prog = Program(
        mov(eax, 0),
        label,
        inc(eax),
        cmp(eax, 100),
        jl(label),
        ret(),
    )
    fun = prog.compile(c_int)
    assert fun() == 100

if __name__ == '__main__':
    test()
