# -*- coding: utf-8 -*-

"""
    repulse
    ~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

import random
from ctypes import c_float, c_int, c_uint, POINTER

from pyasm.macro import log
from pyasm import Program, Label
from pyasm.instructions import (
    add, mul, sub,
    jl, ja, jb, jbe, jmp,
    cmp,
    push, mov, ret, pop,
    fld, fmul, fstp, fsub, fsubr, faddp,
    fadd, fcomi, fsqrt, fdiv, fdivp, fdivr, fmulp, fcmovb,
)
from pyasm.registers import eax, ebx, ecx, edx, esp, ebp, st

def compile():
    outer_loop = Label()
    inner_loop = Label()
    distance_condition = Label()
    distance_else = Label()
    min_condition = Label()
    size_condition = Label()

    prog = Program(
        push(ebp),
        mov(ebp, esp),

        mov(eax, ebp.addr+8), #size
        cmp(eax, 2),
        jl(size_condition),

        mov(ecx, ebp.addr+12), #array pointer

        fld(ebp.addr+16), #force factor
        fld(ebp.addr+20), #minimum distance
        fld(ebp.addr+24), #maximum distance

        sub(eax, 1),
        mov(ebx, 4*4),
        mul(ebx),
        add(ecx, eax),

        mov(eax, ebp.addr+12), #array pointer

        outer_loop,
            mov(ebx, eax),
            add(ebx, 4*4),
            inner_loop,
                # x vector
                fld(eax.addr+0*4),
                fsub(ebx.addr+0*4),
                # y vector 
                fld(eax.addr+1*4),
                fsub(ebx.addr+1*4),
                # distance
                fld(st(1)), 
                fmul(st(0), st(0)),
                fld(st(1)), 
                fmul(st(0), st(0)),
                faddp(),
                fsqrt(),
                #make sure the distance is bigger then 10
                fcomi(st(4)),
                fcmovb(st(4)),
                #only calculate if the distance is less then 200
                fcomi(st(3)),
                ja(distance_condition),
                    #cube distance
                    fld(st(0)),
                    fmul(st(1), st(0)),
                    fmulp(),
                    #compute force vector
                    fdiv(st(2), st(0)),
                    fdivp(),
                    fld(st(4)),
                    fmul(st(2), st(0)),
                    fmulp(),
                    #accumulate y component
                    fld(st(0)),
                    fadd(eax.addr+3*4),
                    fstp(eax.addr+3*4),
                    fsubr(ebx.addr+3*4),
                    fstp(ebx.addr+3*4),
                    #accumulate x component
                    fld(st(0)),
                    fadd(eax.addr+2*4),
                    fstp(eax.addr+2*4),
                    fsubr(ebx.addr+2*4),
                    fstp(ebx.addr+2*4),
                jmp(distance_else),
                distance_condition,
                    fstp(st(0)),
                    fstp(st(0)),
                    fstp(st(0)),
                distance_else,
            add(ebx, 4*4),
            cmp(ebx, ecx),
            jbe(inner_loop),
        add(eax, 4*4),
        cmp(eax, ecx),
        jb(outer_loop),
        
        #restore the fpu
        fstp(st(0)),
        fstp(st(0)),
        fstp(st(0)),

        size_condition,
        
        pop(ebp),
        ret(),
    )

    fun = prog.compile(argtypes=[
        c_int,
        POINTER(c_float),
        c_float,
        c_float,
        c_float,
    ])

    return fun

def make_data(size):
    data = (c_float*(size*4))()
    for i in range(size):
        data[i*4+0] = random.random() * 100
        data[i*4+1] = random.random() * 100
    return data

def test():
    size = 30
    result1 = (c_float*(size*4))()
    result2 = (c_float*(size*4))()
    result1[:] = result2[:] = make_data(size)
    fun = compile()

    fun(size, result1, 120000, 10, 200)
    reference(size, result2, 120000.0, 10.0, 200.0)
    print result1[:]
    print result2[:]
    assert result1[:] == result2[:]
    
def reference(size, data, force_factor, min_distance, max_distance):
    from math import sqrt
    if size >= 2:
        for i in range(size):
            for j in range(i+1, size):
                vx = data[i*4+0] - data[j*4+0]
                vy = data[i*4+1] - data[j*4+1]
                distance = sqrt(vx**2 + vy**2)
                #distance = max(min_distance, sqrt(vx*vx + vy*vy))
                if distance < min_distance:
                    distance = min_distance
                if distance < max_distance:
                    distance = distance**3
                    ux = (vx*force_factor)/distance
                    uy = (vy*force_factor)/distance
                    data[i*4+2] += ux
                    data[i*4+3] += uy
                    data[j*4+2] -= ux
                    data[j*4+3] -= uy

if __name__ == '__main__':
    test()
