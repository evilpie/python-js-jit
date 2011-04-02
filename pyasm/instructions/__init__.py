# -*- coding: utf-8 -*-

"""
    pyasm.instructions.__init__
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm.instructions.basic import bytes
from pyasm.instructions.string import mov, cmova, cmovb, lea
from pyasm.instructions.stack import push, pop, pushfd, popfd
from pyasm.instructions.math import add, sub, inc, dec, mul, not_, neg, shr, sar, shl, xor
from pyasm.instructions.control import (
    ret, call, interrupt,
    jmp,
    je, jne, ja, jl, jle, jb, jbe, ja, jae, jg, jc, jnc, jnz, jz,
    nop,
)
from pyasm.instructions.conditional import cmp, test
from pyasm.instructions.fpu import (
    fmul, fmulp, fdiv, fdivp, fdivr,
    fsub, fsubr, fadd, faddp,
    fld, fst, fstp, fdecstp,
    fcomi,
    fsqrt,
    fcmovb,
)
from pyasm.instructions.sse import (
    movd,
    movups,

    cvtsi2sd,
    cvttsd2si,

    cvtsi2ss,

    addsd,
    addpd,
    pxor,
    paddd,
    psubd,

    subps,
    addps,

    subsd
)
