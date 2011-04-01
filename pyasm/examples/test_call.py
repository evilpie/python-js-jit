# -*- coding: utf-8 -*-

"""
    call
    ~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_int, c_float

from pyasm import Program
from pyasm.data import function
from pyasm.instructions import push, mov, ret, pop, add, call, fld, sub, fstp
from pyasm.registers import eax, ebx, esp, ebp

called = False

@function(None, c_int)
def foo(value):
    global called
    called = value

@function(None, c_float)
def bar(value):
    global called
    called = value

def test():
    prog = Program(
        push(ebp),
        mov(ebp, esp),

        mov(eax, foo),
        push(1234),
        call(eax),
        add(esp, 4),
        
        pop(ebp),
        ret(),
    )
    fun = prog.compile()
    fun()
    assert called == 1234

def test_float():
    prog = Program(
        push(ebp),
        mov(ebp, esp),
        
        fld(ebp.addr+8),
        sub(esp, 4),
        mov(ebp, esp),
        fstp(ebp.addr),
        mov(eax, bar),
        call(eax),
        add(esp, 4),
        
        pop(ebp),
        ret(),
    )
    fun = prog.compile(None, [c_float])
    fun(1234.5)
    assert called == 1234.5
    

if __name__ == '__main__':
    test_float()
