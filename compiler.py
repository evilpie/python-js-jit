from ctypes import *

from pyasm import Program, Label
import pyasm.instructions
from pyasm.instructions import *
from pyasm.registers import DWordRegister, al, ah, eax, esp, ebp, ebx, edx, ecx, esi, xmm0, xmm1, xmm2, xmm3
from pyasm.base import Address
from pyasm.data import function, String

from jsparser import parse

from struct import *
from data import *
from frame import *


class AssemblerWrapper:
    def __init__(self, assembler):
        self.assembler = assembler

        for op in dir(pyasm.instructions):
            if op.startswith('__'):
                continue

            def wrapper(op):
                def inside(self, *args):
                    self.assembler.add(getattr(pyasm.instructions, op)(*args))

                return inside

            AssemblerWrapper.__dict__[op] = wrapper(op)

    def add_(self, a):
        self.assembler.add(a)

    def compile(self, *args):
        return self.assembler.compile(*args)

class Compiler:
    def __init__(self, assembler, rt):
        self.assembler = AssemblerWrapper(assembler)
        self.frame = Frame(self.assembler)
        self.constant_pool = []

        self.objects = (c_int * 20)()

        self.rt = rt # runtime
        self.state = {
            'with': False,
            'eval': False
        }

        self.vars = {}
        self.var_space = None

        self.return_value = BoxedInt(null_value)

    def declare_vars(self, vars):
        index = 0

        for var in vars:
            if var.name not in self.vars:
                self.vars[var.name] = index
                index = index + 1

        self.var_space = (c_int * index)()
        self.var_space[:] = [undefined_value] * index

    def compile(self, ast):
        assert ast.type == 'SCRIPT'

        self.declare_vars(ast.varDecls)

        self.ptr_to_spill = c_int(0)

        self.assembler.push(ebp)
        self.assembler.mov(ebp, esp)
        self.assembler.push(esi)
        self.assembler.mov(esi, addressof(self.ptr_to_spill))
        self.assembler.mov(esi, esi.addr + 0)

        self.op_block(ast)

        self.assembler.pop(esi)
        self.assembler.pop(ebp)
        self.assembler.ret()

        self.spill_memory = (c_int * self.frame.spill_index)()
        self.ptr_to_spill.value = addressof(self.spill_memory)

        return self.assembler.compile()

    def box(self, v, target):
        if v.is_constant():
            if v.is_int():
                self.assembler.mov(target, integer_value(v.value))
            elif v.is_double():
                double = new_double(v.value)
                self.assembler.mov(target, object_value(double))
            else:
                self.assembler.mov(target, object_value(v.value))
        else:
            if v.is_int():
                reg = v.to_reg()
                self.assembler.shl(reg, 1)
                self.assembler.mov(target, reg)
            elif v.is_double():
                assert False
            elif v.is_unknown():
                reg = v.to_reg()
                if reg != target:
                    self.assembler.mov(target, reg)
            else:
                reg = v.to_reg()
                self.assembler.shl(reg, 1)
                self.assembler.add(reg, 1)
                if target != reg:
                    self.assembler.mov(target, reg)

    def jump_not_int(self, reg, jump):
        self.assembler.test(reg, 1)
        self.assembler.jnz(jump)

    def compile_node(self, node):
        getattr(self, 'op_' + node.type.lower())(node)

    def op_comma(self, nodes):
        for node in nodes[:-1]:
            self.compile_node(node)
            self.frame.pop()

        self.compile_node(nodes[-1])

    def op_block(self, nodes):
        for node in nodes:
            self.compile_node(node)

    def op_group(self, node):
        self.compile_node(node[0])

    def op_semicolon(self, node):
        self.compile_node(node.expression)
        self.frame.pop()

    def op_number(self, node):
        value = node.value

        if isinstance(value, int):
            self.frame.push_int(value)
        else:
            self.frame.push_double(value)

    def op_string(self, node):
        value = node.value

        str = new_string(value)
        self.constant_pool.append(str)
        self.frame.push_string(addressof(str))

    def op_true(self, node):
        self.frame.push_bool(True)

    def op_false(self, node):
        self.frame.push_bool(False)

    def op_null(self, node):
        self.frame.push_null()

    def op_array_init(self, nodes):
        for node in nodes:
            if node: # could be hole
                self.compile_node(node)

        @function(c_int, c_int)
        def array_init(size):
            obj = new_array(size)
            self.constant_pool.append(obj)

            return addressof(obj)

        size = len(nodes)

        self.frame.spill_all()

        self.assembler.push(size)
        self.assembler.mov(self.frame.scratch, array_init)
        self.assembler.call(self.frame.scratch)
        self.assembler.add(esp, 4)

        self.assembler.push(eax)  #fixme

        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax.addr + 8) # elements

        i = size - 1
        for node in nodes:
            if node:
                element = self.frame.peek(-(size - i))
                self.box(element, self.frame.scratch)
                self.assembler.mov(reg.addr + i * 4, self.frame.scratch)
            else:
                self.assembler.mov(reg.addr + i * 4, undefined_value) # todo: needs special value
            i = i - 1

        self.frame.free_reg(reg)
        reg = self.frame.alloc_reg()
        self.assembler.pop(self.frame.scratch)
        self.assembler.mov(reg, eax)
        self.frame.push('object', reg)


    def op_unary_minus(self, node):
        self.compile_node(node[0])

        lhs = self.frame.peek(-1)
        if lhs.is_constant():
            self.frame.pop()

            if lhs.is_int():
                self.frame.push_int(-lhs.value)
            elif lhs.is_double():
                self.frame.push_double(-lhs.value)
            elif lhs.is_string():
                new = self.rt.sub(boxed_integer(0), boxed_object(lhs))
                if new.isInteger():
                    self.frame.push_int(new.toInteger())
                else:
                    self.frame.push_double(new.toObject().to(PrimitiveDouble).value)
            elif lhs.is_null():
                self.frame.push_double(-0)
            elif lhs.is_undefined():
                self.frame.push_double(float('nan'))
        elif lhs.is_int():
            reg = lhs.to_reg()
            self.frame.pop()

            self.assembler.neg(reg)
            self.frame.push('int', reg)
        else:
            @function(c_int, BoxedInt)
            def unary_minus(lhs):
                return self.rt.sub(boxed_integer(0), lhs).value

            self.call(unary_minus, lhs)

            result = self.frame.alloc_reg()
            self.assembler.mov(result, eax)

            self.frame.pop()
            self.frame.push('unknown', result)

    def op_unary_plus(self, node):
        self.compile_node(node[0])

        lhs = self.frame.peek(-1)

        if lhs.is_int() or lhs.is_double():
            return # nothing to do

        if lhs.is_constant():
            if lhs.is_null():
                self.frame.pop()
                self.frame.push_int(0)
            elif lhs.is_undefined():
                self.frame.pop()
                self.frame.push_double(float('nan'))
            elif lhs.is_bool():
                self.frame.pop()
                self.frame.push_int(0 + lhs.value)
            else:
                raise NotImplementedError('op unary plus constant folding')
        else:
            reg = lhs.to_reg()
            if lhs.is_bool():
                self.frame.pop()
                self.frame.push('int', eax) # true is 1 and false is 0 already
            else:
                raise NotImplementedError('op unary plus')

    def op_not(self, node):
        self.compile_node(node[0])

        lhs = self.frame.peek(-1)

        if lhs.is_constant():
            self.frame.pop()

            if lhs.is_bool():
                self.frame.push_bool(not lhs.value)
            elif lhs.is_int():
                self.frame.push_bool(lhs.value == 0)
            elif lhs.is_double():
                if math.isnan(lhs.value):
                    self.frame.push_bool(True)
                else:
                    self.frame.push_bool(lhs.value == 0)
            elif lhs.is_null() or lhs.is_undefined():
                self.frame.push_bool(True)
            elif lhs.is_object():
                self.frame.push_bool(False)
            else:
                raise NotImplementedError('op not')
        elif lhs.is_object():
            self.frame.pop()
            self.frame.push_bool(False)
        else:
            reg = lhs.to_reg()
            if lhs.is_bool():
                self.assembler.xor(reg, 1)
            elif lhs.is_int():
                self.assembler.cmp(reg, 0)
                self.assembler.xor(reg, reg)
                self.assembler.jne(end)
                self.assembler.mov(reg, 1)
                self.assembler.add_(end)
            else:
                raise NotImplementedError('op not')

            self.frame.pop()
            self.frame.take_reg(reg)
            self.frame.push('bool', reg)

    def op_void(self, node):
        self.compile_node(node[0])
        lhs = self.frame.peek(-1)

        @function(None, BoxedInt)
        def log(v):
            print 'void stub (logging)'
            dump_boxed_int(v)

        self.call(log, lhs)

        self.frame.pop()
        self.frame.push_undefined()

    def op_plus(self, node):
        self.op_binary(node, 'add')
    def op_minus(self, node):
        self.op_binary(node, 'sub')

    def op_binary(self, node, op):
        self.compile_node(node[0])
        self.compile_node(node[1])

        rhs = self.frame.peek(-1)
        lhs = self.frame.peek(-2)

        if lhs.is_constant() and rhs.is_constant():
            value = getattr(self.rt, op)(lhs.to_boxed_int(), rhs.to_boxed_int())

            self.frame.pop()
            self.frame.pop()
            self.frame.push_boxed_int(value)
            return

        if lhs.is_int() and rhs.is_int():
            reg1 = rhs.to_reg()
            reg2 = lhs.to_reg()

            getattr(self.assembler, op)(reg1, reg2)

            self.frame.pop()
            self.frame.pop()
            self.frame.push('int', reg1)
            return


        @function(c_int, BoxedInt, BoxedInt)
        def add_stub(lhs, rhs):
            return self.rt.add(lhs, rhs).value

        @function(c_int, BoxedInt, BoxedInt)
        def sub_stub(lhs, rhs):
            return self.rt.sub(lhs, rhs).value

        stubs = {
            'add': add_stub,
            'sub': sub_stub
        }

        self.call(stubs[op], lhs, rhs)

        self.frame.pop()
        self.frame.pop()
        result = self.frame.alloc_reg()
        self.assembler.mov(result, eax)
        self.frame.push('unknown', result)

    def op_eq(self, node):
        self.compile_node(node[0])
        self.compile_node(node[1])

        rhs = self.frame.peek(-1)
        lhs = self.frame.peek(-2)

        if lhs.is_constant() and rhs.is_constant():
            equal = self.rt.equality(lhs.to_boxed_int(), rhs.to_boxed_int())

            self.frame.pop()
            self.frame.pop()

            if equal:
                self.frame.push_bool(True)
            else:
                self.frame.push_bool(False)
        elif (lhs.is_int() or lhs.is_bool()) and (rhs.is_int() or rhs.is_bool()):
            end = Label('end')
            equal = Label('equal')

            reg1 = rhs.to_reg()
            reg2 = lhs.to_reg()

            self.assembler.cmp(reg1, reg2)
            self.assembler.je(equal)
            self.assembler.mov(reg1, 0)
            self.assembler.jmp(end)
            self.assembler.add_(equal)
            self.assembler.mov(reg1, 1)
            self.assembler.add_(end)

            self.frame.pop()
            self.frame.pop()
            self.frame.push('bool', reg1)
        elif lhs == rhs == 'double':
            end = Label('end')

            #todo: fix for NaN
            self.assembler.mov(eax, ebx.addr + 4)
            self.assembler.mov(edx, ecx.addr + 4)
            self.assembler.mov(ebx, 1)
            self.assembler.cmp(eax, edx)
            self.assembler.je(end)
            self.assembler.mov(ebx, 0)
            self.assembler.add_(end)

            self.frame.push('bool', ebx)
        else:

            @function(c_int, BoxedInt, BoxedInt)
            def eq(lhs, rhs):
                return 1 if self.rt.equality(lhs, rhs) else 0

            self.call(eq, lhs, rhs)

            self.frame.pop()
            self.frame.pop()

            reg = self.frame.alloc_reg()
            self.assembler.mov(reg, eax)

            self.frame.push('bool', reg)


    def conditional(self, cond_node, if_node, else_node, else_jump=None):
        self.compile_node(cond_node)

        if_part = Label('if part')
        else_part = Label('else part')
        end = Label('end')

        cond = self.frame.peek(-1)
        if cond.is_constant():
            boolean = self.rt.toBoolean(cond.to_boxed_int())
            self.frame.spill_all(forget=True)

            if boolean.toBool() == True:
                self.compile_node(if_node)
            else:
                if else_jump:
                    self.assembler.jmp(else_jump)
                elif else_node:
                    self.assembler.compile_node(else_node)
        else:
            self.frame.spill_all(forget=True)

            @function(c_int, BoxedInt)
            def stub_conditional(condition):
                print 'stub conditional'
                return self.rt.toBoolean(condition).value

            test = Label('test')
            stub = Label('stub')

            reg = cond.to_reg()

            self.assembler.add_(test)
            #test for bool
            self.assembler.cmp(reg, true_value)
            self.assembler.je(if_part)
            self.assembler.cmp(reg, false_value)
            self.assembler.je(else_part)

            #test for int
            self.jump_not_int(reg, stub)
            self.assembler.cmp(reg, 0)
            self.assembler.jne(if_part)
            self.assembler.jmp(else_part)

            #stub
            self.assembler.add_(stub)
            self.call(stub_conditional, cond)
            self.assembler.mov(reg, eax)
            self.assembler.jmp(test)


        #else part
        if else_node:
            self.assembler.add_(else_part)
            self.compile_node(else_node)
            self.assembler.jmp(end)
        elif else_jump:
            self.assembler.add_(else_part)
            self.assembler.jmp(else_jump)
        else:
            self.assembler.add_(else_part)
            self.assembler.jmp(end)

        #if part
        self.assembler.add_(if_part)
        self.compile_node(if_node)
        self.assembler.add_(end)

    def op_if(self, node):
        self.conditional(node.condition, node.thenPart, node.elsePart)

    def op_hook(self, node):
        self.conditional(node[0], node[1], node[2])

    def op_for(self, node):
        if node.setup:
            self.compile_node(node.setup)

        start = Label('start')
        end = Label('end')
        self.assembler.add_(start)

        if node.condition:
            self.conditional(node.condition, node.body, None, else_jump=end)

        if node.update:
            self.compile_node(node.update)
            self.frame.pop()

        self.assembler.jmp(start)
        self.assembler.add_(end)

    def op_increment(self, node):
        type = node[0].type.lower()

        if type == 'identifier':
            self.increment_identifier(node, -1)

    def op_decrement(self, node):
        type = node[0].type.lower()

        if type == 'identifier':
            self.increment_identifier(node, 1)

    def increment_identifier(self, node, amount):
        self.op_identifier(node[0])
        if hasattr(node, 'postfix'):
            self.op_identifier(node[0]) # todo this should be self.frame.duplicate or simliar

        self.frame.push_int(amount)

        class Nop:
            type = 'NOP'

        self.op_minus({
            0 : Nop,
            1 : Nop
        })

        self.op_assign({
            0 : node[0],
            1 : Nop
        })

        if hasattr(node, 'postfix'):
            self.frame.pop()


    def op_assign(self, node):
        type = node[0].type.lower()

        if type == 'identifier':
            self.assign_identifier(node)
        elif type == 'index':
            self.assign_index(node)
        else:
            assert 'not done yet', False

    def op_var(self, nodes):
        for node in nodes:
            if not hasattr(node, 'initializer'):
                continue

            name = node.name
            if not name in self.vars:
                raise 'var not declared'

            index = self.vars[name]

            self.compile_node(node.initializer)
            rhs = self.frame.peek(-1)

            self.assembler.mov(self.frame.scratch, addressof(self.var_space))
            self.box(rhs, self.frame.scratch.addr + index * 4)

            self.frame.pop()

    def assign_identifier(self, node):
        name = node[0].value

        if not name in self.vars:
            raise 'var not declared'

        index = self.vars[name]

        self.compile_node(node[1])
        rhs = self.frame.peek(-1)

        if rhs.is_unknown():
            reg = rhs.to_reg()

            self.assembler.mov(self.frame.scratch, addressof(self.var_space))
            self.assembler.mov(self.frame.scratch.addr + index * 4, reg)

            self.frame.pop()
            self.frame.take_reg(reg) # pop would free the |reg|
            self.frame.push('unknown', reg)

        elif rhs.is_constant():
            boxed = rhs.to_boxed_int()

            self.assembler.mov(self.frame.scratch, addressof(self.var_space))
            self.assembler.mov(self.frame.scratch.addr + index * 4, boxed.value)

            self.frame.pop()
            self.frame.push_boxed_int(boxed)
        else:
            reg = rhs.to_reg()

            self.box(rhs, reg)
            self.assembler.mov(self.frame.scratch, addressof(self.var_space))
            self.assembler.mov(self.frame.scratch.addr + index * 4, reg)

            self.frame.pop()
            self.frame.take_reg(reg)
            self.frame.push(rhs.type, reg)

    def assign_index(self, node):
        self.compile_node(node[0][0])
        self.compile_node(node[0][1])
        self.compile_node(node[1])

        value = self.frame.pop(ecx)
        index = self.frame.pop(ebx)
        obj = self.frame.pop(eax)

        @function(c_int, BoxedInt, BoxedInt, BoxedInt)
        def assign(obj, index, value):
            print 'stub assign index', obj, index, value

            if index.isInteger():
                id = index.toInteger()
            else:
                assert 'bla blub', False

            if obj.isObject():
                obj = obj.toObject()
                if obj.isArray():
                    array = obj.to(ArrayObject)
                    if id < array.length:
                        array.setElement(id, value.value)

            return value.value

        self.box(value, ecx)
        self.assembler.push(ecx)
        self.box(index, ebx)
        self.assembler.push(ebx)
        self.box(obj, eax)
        self.assembler.push(eax)

        self.assembler.mov(eax, assign)
        self.assembler.call(eax)
        self.assembler.add(esp, 12)

        self.frame.push('unknown', eax)

    def op_identifier(self, node):
        name = node.value

        if name not in self.vars:
            raise 'var not declared'

        index = self.vars[name]

        reg = self.frame.alloc_reg()
        self.assembler.mov(self.frame.scratch, addressof(self.var_space))
        self.assembler.mov(reg, self.frame.scratch.addr + index * 4)

        self.frame.push('unknown', reg)

    def op_dot(self, node):
        self.compile_node(node[0])

        @function(c_int, c_int, BoxedInt)
        def dot(index, base):
            print 'stub dot', index, base
            property = self.names[index]

            if base.isObject():
                obj = base.toObject()
                if obj.isString():
                    if property == 'length':
                        return integer_value(len(obj.toPrimitive()))

                if obj.isArray():
                    if property == 'length':
                        return integer_value(obj.to(ArrayObject).length)

            return integer_value(0xdead)

        self.names.append(node[1].value)
        index = len(self.names) - 1

        lhs = self.frame.pop(eax)

        self.assembler.push(eax)
        self.assembler.push(index)
        self.assembler.mov(eax, dot)
        self.assembler.call(eax)
        self.assembler.add(esp, 8)

        self.frame.push('unknown', eax)

    def op_index(self, node):
        self.compile_node(node[0])
        self.compile_node(node[1])

        rhs = self.frame.pop(ebx)
        lhs = self.frame.pop(eax)

        @function(c_int, c_int, BoxedInt)
        def index_int(index, base):
            print 'stub index int', index, base

            if base.isObject():
                obj = base.toObject()
                if obj.isString():
                    string = obj.toPrimitive()
                    if index < len(string):
                        o = new_string(string[index])
                        self.constant_pool.append(o)
                        return object_value(addressof(o))

                if obj.isArray():
                    array = obj.to(ArrayObject)
                    if index < array.length and array.hasElements():
                        return array.element(index)

            return integer_value(11111)

        if rhs == 'int':
            self.assembler.push(eax)
            self.assembler.push(ebx)
            self.assembler.mov(eax, index_int)
            self.assembler.call(eax)
            self.assembler.add(esp, 8)

            self.frame.push('unknown', eax)

        else:
            raise NotImplementedError('non int index')


    def op_typeof(self, node):
        self.compile_node(node[0])

        t = self.frame.peek(-1)
        if not t.is_unknown() and not t.is_object():
            self.frame.pop()
            if t.is_null():
                str = self.rt.strings['null']
            elif t.is_undefined():
                str = self.rt.strings['undefined']
            elif t.is_int() or t.is_double():
                str = self.rt.strings['number']
            elif t.is_string():
                str = self.rt.strings['string']

            self.frame.push_string(addressof(str))
        else:

            @function(c_int, BoxedInt)
            def typeof(v):
                return addressof(self.rt.typeof(v))

            self.call(typeof, t)
            self.frame.push('string', eax)

    def op_nop(self, node):
        pass

    def call(self, function, *args):

        for arg in args[::-1]:
            self.box(arg, self.frame.scratch)
            self.assembler.push(self.frame.scratch)

        self.frame.spill_all()
        #self.frame.take_reg(eax) todo scratch is eax for now

        self.assembler.mov(self.frame.scratch, function)
        self.assembler.call(self.frame.scratch)
        self.assembler.add(esp, len(args) * 4)


def main():
    import sys
    from runtime import Runtime

    file = sys.argv[1]
    code = open(file).read()

    asm = Program()
    runtime = Runtime()
    compiler = Compiler(asm, runtime)

    ast = parse(code)
    print ast

    fptr = compiler.compile(ast)
    fptr()

    print ""
    print " === Returned === "
    dump_boxed_int(compiler.return_value)

main()
