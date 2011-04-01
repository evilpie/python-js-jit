# -*- coding: utf-8 -*-

"""
    copy
    ~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Program
from pyasm.macro import syscall
from pyasm.instructions import mov, ret
from pyasm.registers import ebx
import sys

def example():
    prog = Program(
        mov(ebx, 42),
        syscall('exit'),
    )
    fun = prog.compile()
    fun()

if __name__ == '__main__':
    example()
