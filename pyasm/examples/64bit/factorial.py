# -*- coding: utf-8 -*-
"""
    factorial
    ~~~~~~~~~

    :copyright: 2008 by Henri Tuhola <henri.tuhola@gmail.com>
    :license: GNU AGPL v3 or later, see LICENSE for more details.    
"""

from ctypes import POINTER, c_long

from pyasm import Program
from pyasm.base import Label
from pyasm.instructions import mov, mul, dec, cmp, jg, ret
from pyasm.registers import rax, rdi

def factorial(value):
    accum = 1
    while value > 1:
        accum *= value
        value -= 1
    return accum

if __name__ == '__main__':
    loop = Label()
    prog = Program(
        mov(rax, 1),
        loop,
        mul(rax, rdi),
        dec(rdi),
        cmp(rax, 1),
        ja(loop),
        ret()
    )
    fun = prog.compile(restype=c_long, argtypes=[c_long])

    for i in xrange(20):
        assert fun(i) == factorial(i)
