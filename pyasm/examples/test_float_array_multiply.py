# -*- coding: utf-8 -*-

"""
    float_array_multiply
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_float, c_int, POINTER

from pyasm import Program, Label
from pyasm.instructions import (
    add, dec,
    jg,
    cmp,
    push, mov, ret, pop,
    fld, fmul, fstp,
)
from pyasm.registers import eax, ebx, ecx, edx, esp, ebp

def test():
    loop = Label()
    prog = Program(
        push(ebp),
        mov(ebp, esp),
        mov(eax, ebp.addr+8),
        mov(ebx, ebp.addr+12),
        mov(ecx, ebp.addr+16),
        mov(edx, ebp.addr+20),
        loop,
            fld(ebx.addr),
            fmul(ecx.addr),
            fstp(edx.addr),
            add(ebx, 4),
            add(ecx, 4),
            add(edx, 4),
            dec(eax),
        cmp(eax, 0),
        jg(loop),
        pop(ebp),
        ret(),
    )
   
    fun = prog.compile(argtypes=[
        c_int,
        POINTER(c_float),
        POINTER(c_float),
        POINTER(c_float),
    ])
   
    size = 1000
    a = (c_float*size)()
    b = (c_float*size)()
    c = (c_float*size)()
    a[:] = range(0, size)
    b[:] = range(size, size*2)
    c[:] = [0] * size
  
    fun(size, a, b, c)
    #weirdly off by 1 for higher result numbers
    for i in range(size):
        assert c[i] == a[i] * b[i]

if __name__ == '__main__':
    test()

