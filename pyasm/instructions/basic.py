# -*- coding: utf-8 -*-

"""
    pyasm.instructions.basic
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Instruction

@Instruction.producer
def bytes(inst, *data):
    for byte in data:
        inst.chr(byte)
