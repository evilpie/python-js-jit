# -*- coding: utf-8 -*-

"""
    call
    ~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_int

from pyasm import Program
from pyasm.macro import log
from pyasm.instructions import push, mov, ret, pop, add, call
from pyasm.registers import eax, ebx, esp, ebp

def test():
    prog = Program(
        push(ebp),
        mov(ebp, esp),

        mov(ebx, 1234),
        log('ebx is', ebx),
        
        pop(ebp),
        ret(),
    )
    fun = prog.compile()
    fun()

if __name__ == '__main__':
    test()
