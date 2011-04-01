# -*- coding: utf-8 -*-

"""
    pyasm.macro
    ~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_int, c_float

from pyasm.base import Register
from pyasm.data import function
from pyasm.instructions import push, mov, call, sub, add, pop, fld, fstp, interrupt
from pyasm.registers import eax, ebx, ecx, edx, esp, ebp, st

def log(name, operand, type=c_int):
    if isinstance(operand, Register):
        if isinstance(operand, st):
            type = c_float
            push_fun = [
                sub(esp, 4),
                mov(ebp, esp),
                fld(operand),
                fstp(ebp.addr),
            ]
        else:
            push_fun = push(operand)
        @function(None, type)
        def _debug(value):
            print(name % value)
        return [
            push(eax),
            push(ebx),
            push(ecx),
            push(edx),
            push(ebp),
            push_fun,
            mov(eax, _debug),
            call(eax),
            add(esp, 4),
            pop(ebp),
            pop(edx),
            pop(ecx),
            pop(ebx),
            pop(eax),
        ]
    else:
        raise Exception('operand is not suited: %s' % operand)

def syscall(name):
    names = dict(
        exit    = 1,
        read    = 3,
        write   = 4,
    )

    return [
        mov(eax, names[name]),
        interrupt(0x80),
    ]
