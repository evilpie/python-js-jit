from pyasm.registers import *
from data import *

class FrameValue:
    def __init__(self, frame):
        self.frame = frame
        self.constant = False
        self.reg = None
        self.memory = None

    def set_constant(self, v, type):
        self.constant = True
        self.type = type
        self.value = v

    def set_register(self, reg, type):
        self.reg = reg
        self.type = type

    def is_constant(self):
        return self.constant

    def in_reg(self):
        return not self.reg is None

    def in_memory(self):
        return not self.memory is None

    def is_int(self):
        return self.type == 'int'
    def is_double(self):
        return self.type == 'double'
    def is_string(self):
        return self.type == 'string'
    def is_object(self):
        return self.type == 'object'
    def is_null(self):
        return self.type == 'null'
    def is_undefined(self):
        return self.type == 'undefined'
    def is_bool(self):
        return self.type == 'bool'
    def is_unknown(self):
        return self.type == 'unknown'

    def unuse(self):
        if self.in_reg():
            self.frame.free_reg(self.reg)
            self.reg = None

    def spill(self, forget=False):
        print 'spill', self.reg, self.memory, self.constant
        if self.in_memory():
            return
        index = self.frame.spill_index
        if self.in_reg():
            self.frame.assembler.mov(esi.addr + index * 4, self.reg)
            self.frame.free_reg(self.reg)
        else:
            assert self.is_constant()
            self.frame.assembler.mov(esi.addr + index * 4, self.to_boxed_int().value)
        self.reg = None
        self.constant = False
        self.memory = index
        if forget:
            self.type = 'unknown'

        self.frame.spill_index += 1

    def to_reg(self):

        print 'to reg', self.reg, self.memory, self.constant

        assert not self.is_constant()
        if self.in_reg():
            return self.reg
        else:
            assert self.in_memory()

            reg = self.frame.alloc_reg()
            self.frame.assembler.mov(reg, esi.addr + self.memory * 4)
            self.reg = reg
            self.memory = None
            self.constant = False

            return reg


    def to_boxed_int(self):
        assert self.is_constant()

        if self.is_int() or self.is_double():
            return boxed_number(self.value)
        elif self.is_string() or self.is_object():
            return boxed_object(self.value)
        elif self.is_bool():
            return boxed_bool(self.value)
        elif self.is_null():
            return BoxedInt(null_value)
        elif self.is_undefined():
            return BoxedInt(undefined_value)

class Frame:
    normal_regs = [ebx, ecx, edx]
    double_regs = [xmm0, xmm1, xmm2, xmm3]
    scratch = eax

    def __init__(self, assembler):
        self.assembler = assembler
        self.stack = []
        self.spill_index = 0
        self.free = Frame.normal_regs[:]

    def alloc_reg(self):
        if self.free:
            return self.free.pop()
        else:
            for v in self.stack:
                if v.in_reg():  # spill oldest
                    reg = v.reg
                    v.spill()
                    self.free.remove(reg)
                    return reg

    def take_reg(self, register):
        if register in self.free:
            self.free.remov(register)
        else:
            for v in self.stack:
                if v.reg == register:
                    v.spill()
            self.free.remov(register)

    def free_reg(self, register):
        assert register not in self.free
        assert isinstance(register, DWordRegister)

        self.free.append(register)

    def spill_all(self, forget=False):
        print 'spill all', self.stack
        for v in self.stack:
            v.spill(forget=forget)

    def push(self, type, register):
        v = FrameValue(self)
        v.set_register(register, type)
        self.stack.append(v)

    def push_string(self, value):
        v = FrameValue(self)
        v.set_constant(value, 'string')
        self.stack.append(v)

    def push_int(self, value):
        v = FrameValue(self)
        v.set_constant(value, 'int')
        self.stack.append(v)

    def push_double(self, value):
        v = FrameValue(self)
        v.set_constant(value, 'double')
        self.stack.append(v)

    def push_undefined(self):
        v = FrameValue(self)
        v.set_constant(3, 'undefined')
        self.stack.append(v)

    def push_null(self):
        v = FrameValue(self)
        v.set_constant(2, 'null')
        self.stack.append(v)

    def push_bool(self, value):
        v = FrameValue(self)
        value = int(bool(value))
        v.set_constant(value, 'bool')
        self.stack.append(v)

    def push_boxed_int(self, value):
        v = FrameValue(self)
        if value.isInteger():
            v.set_constant(value.toInteger(), 'int')
        elif value.isBool():
            v.set_constant(value.toInteger(), 'bool')
        elif value.isNull():
            v.set_constant(2, 'null')
        elif value.isUndefined():
            v.set_constant(3, 'undefined')
        else:
            obj = value.toObject()
            if obj.isDouble():
                v.set_constant(obj.toPrimitive(), 'double')
            elif obj.isString():
                v.set_constant(addressof(obj), 'string')
            else:
                v.set_constant(addressof(obj), 'object')
        self.stack.append(v)

    def peek(self, index):
        return self.stack[index]

    def pop(self):
        v = self.stack[-1]
        if v.in_reg():
            self.free_reg(v.reg)
        self.stack.pop()
