# -*- coding: utf-8 -*-
"""
    factorial
    ~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>
    :license: GNU AGPL v3 or later, see LICENSE for more details.    
"""

from ctypes import c_int

from pyasm import Program, Label
from pyasm.instructions import (
    inc, dec, mul,
    jl, jmp, ret,
    mov, cmp, push, pop
)
from pyasm.registers import eax, ebx, ebp, esp

def factorial(value):
    accum = 1
    while value > 1:
        accum *= value
        value -= 1
    return accum

def test():
    start = Label()
    end = Label()

    prog = Program(
        push(ebp),
        mov(ebp, esp),
        mov(ebx, ebp.addr+8),
        mov(eax, 1),
        start,
        cmp(ebx, 1),
        jl(end),
        mul(ebx),
        dec(ebx),
        jmp(start),
        end,
        pop(ebp),
        ret(),
    )
    fun = prog.compile(restype=c_int, argtypes=[c_int])

    for i in range(13): #factorial of 12 is the maximum integer fitting a 32 bit register
        assert fun(i) == factorial(i)

if __name__ == '__main__':
    test()
