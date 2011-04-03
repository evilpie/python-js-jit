# -*- coding: utf-8 -*-

"""
    pyasm.registers
    ~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm.base import Register
from pyasm.exceptions import AssemblyError

class ByteRegister(Register): pass
class DWordRegister(Register): pass
class QWordRegister(Register): pass
class XMMRegister(Register): pass

al = ByteRegister('al', 0)
ah = ByteRegister('ah', 4)

eax = DWordRegister('eax', 0)
ecx = DWordRegister('ecx', 1)
edx = DWordRegister('edx', 2)
ebx = DWordRegister('ebx', 3)
esp = DWordRegister('esp', 4)
ebp = DWordRegister('ebp', 5)
esi = DWordRegister('esi', 6)
edi = DWordRegister('edi', 7)

rax = QWordRegister('rax', 0)
rsi = QWordRegister('rsi', 6)
rdi = QWordRegister('rdi', 7)

class st(Register):
    def __init__(self, n):
        if n > 7:
            raise AssemblyError('x87 has only 7 registers')
        Register.__init__(self, 'st(%i)' % n, n)


xmm0 = XMMRegister('xmm0', 0)
xmm1 = XMMRegister('xmm1', 1)
xmm2 = XMMRegister('xmm2', 2)
xmm3 = XMMRegister('xmm3', 3)
xmm4 = XMMRegister('xmm4', 4)
xmm5 = XMMRegister('xmm5', 5)
xmm6 = XMMRegister('xmm6', 6)
xmm7 = XMMRegister('xmm7', 7)
