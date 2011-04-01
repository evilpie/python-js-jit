# -*- coding: utf-8 -*-

"""
    copy
    ~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Program
from pyasm.data import String
from pyasm.macro import syscall
from pyasm.instructions import mov, ret, push, add
from pyasm.registers import eax, ebx, ecx, edx, ebp
import sys

def example():
    msg = 'Hello World!'
    prog = Program(
        mov(ebx, 1),
        mov(ecx, String(msg)),
        mov(edx, len(msg)),
        syscall('write'),
        ret(),
    )
    fun = prog.compile()
    fun()

if __name__ == '__main__':
    example()
