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
from frame import Frame
from context import Context

from object import Value, ObjectFactory

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
    def __init__(self, assembler, rt, ctx):
        self.assembler = AssemblerWrapper(assembler)
        self.frame = Frame(self.assembler)

        self.rt = rt # runtime
        self.ctx = ctx
        self.state = {
            'with': False,
            'eval': False
        }

    def declare_vars(self, vars):
        for var in vars:
            self.ctx.object.addProperty(var.name, Value(Value.undefined))

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

        print self.assembler.assembler

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
                v.type = 'unknown' # fixme
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
                v.type = 'unknown'
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
        def array_init(length):
            array = ObjectFactory.createArray(length)
            return array.pointer

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

        for node in nodes:
            if node:
                self.frame.pop()

        self.assembler.pop(self.frame.scratch)
        self.assembler.mov(reg, self.frame.scratch)
        self.frame.push('object', reg)

    def op_object_init(self, nodes):
        @function(c_int)
        def object_init():
            obj = ObjectFactory.createPlain(0, len(nodes) + 2)
            return obj.pointer

        self.call(object_init)
        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)

        self.frame.push('object', reg)

        @function(None, Value, Value, Value)
        def add_property(obj, key, value):
            obj = obj.toObject()

            name = self.rt.toString(key)
            str = name.toObject().toString()

            obj.addProperty(str, value)

        for node in nodes:
            string = new_string(str(node[0].value))
            self.frame.push_string(addressof(string))
            self.compile_node(node[1])

            obj = self.frame.peek(-3)
            key = self.frame.peek(-2)
            value = self.frame.peek(-1)

            self.call(add_property, obj, key, value)

            self.frame.pop()
            self.frame.pop()

        # the object pointers stays on the stack

    def op_function(self, node):
        assert 0

    def op_this(self, nodes):

        @function(c_int)
        def this():
            return self.ctx.this.raw

        self.call(this)
        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)

        self.frame.push('unknown', reg)

    def op_unary_minus(self, node):
        self.compile_node(node[0])

        lhs = self.frame.peek(-1)
        if lhs.is_constant():
            self.frame.pop()
            value = self.rt.sub(boxed_integer(0), lhs.to_boxed_int())
            self.push_boxed_int(value)
        elif lhs.is_int():
            reg = lhs.to_reg()
            self.frame.pop()
            self.frame.take_reg(reg)
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
            self.frame.pop()
            value = self.rt.toNumber(lhs.to_boxed_int())
            self.frame.push_boxed_int(value)
        else:
            reg = lhs.to_reg()
            if lhs.is_bool():
                self.frame.pop()
                self.frame.take_reg(reg)
                self.frame.push('int', reg) # true is 1 and false is 0 already
            else:
                @function(c_int, BoxedInt)
                def unary_plus(lhs):
                    return self.rt.toNumber(lhs).value

                self.call(unary_plus, lhs)

                result = self.frame.alloc_reg()
                self.assembler.mov(result, eax)

                self.frame.pop()
                self.frame.push('unknown', result)

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

        @function(None, Value)
        def log(v):
            print 'void stub (logging)'
            v.dump()

        self.call(log, lhs)

        self.frame.pop()
        self.frame.push_undefined()

    def op_plus(self, node):
        self.binary(node, 'add')
    def op_minus(self, node):
        self.binary(node, 'sub')

    def binary(self, node, op):
        self.compile_node(node[0])
        self.compile_node(node[1])

        rhs = self.frame.peek(-1)
        lhs = self.frame.peek(-2)

        if lhs.is_constant() and rhs.is_constant():
            value = getattr(self.rt, op)(lhs.to_boxed_int(), rhs.to_boxed_int())

            self.frame.pop()
            self.frame.pop()
            self.frame.push_boxed_int(value)
        elif lhs.is_int() and rhs.is_int():
            reg1 = rhs.to_reg()
            reg2 = lhs.to_reg()

            getattr(self.assembler, op)(reg1, reg2)

            self.frame.pop()
            self.frame.pop()
            self.frame.push('int', reg1)
        else:

            @function(c_int, Value, Value)
            def add_stub(lhs, rhs):
                print 'add stub'
                return self.rt.add(lhs, rhs).raw

            @function(c_int, Value, Value)
            def sub_stub(lhs, rhs):
                print 'sub stub'
                return self.rt.sub(lhs, rhs).raw

            result = self.frame.alloc_reg()
            types = ['int', 'unknown']
            stub = Label('stub')
            end = Label('end')

            if lhs.type in types and rhs.type in types:
                    reg1 = reg2 = None
                    not_equal = Label('not equal')

                    if rhs.is_unknown():
                        reg1 = rhs.to_reg()
                        self.jump_not_int(reg1, stub)
                    elif not rhs.is_constant():
                        reg1 = rhs.to_reg()

                    if lhs.is_unknown():
                        reg2 = lhs.to_reg()
                        self.jump_not_int(reg2, stub)
                    elif not rhs.is_constant():
                        reg2 = lhs.to_reg()

                    if reg1 is not None and reg2 is not None:
                        self.assembler.sar(reg1, 1)
                        self.assembler.sar(reg2, 1)
                        self.assembler.mov(result, reg1)
                        getattr(self.assembler, op)(result, reg2)
                        self.assembler.shl(result, 1)

                    if reg1 is None:
                        assert isinstance(rhs.value, int)
                        self.assembler.sar(reg2, 1)
                        self.assembler.mov(result, rhs.value)
                        getattr(self.assembler, op)(result, reg2)
                        self.assembler.shl(result, 1)

                    if reg2 is None:
                        assert isinstance(lhs.value, int)
                        self.assembler.sar(reg1, 1)
                        self.assembler.mov(result, lhs.value)
                        getattr(self.assembler, op)(result, reg1)
                        self.assembler.shl(result, 1)

                    self.assembler.jmp(end)

            stubs = {
                'add': add_stub,
                'sub': sub_stub
            }

            self.assembler.add_(stub)
            self.call(stubs[op], lhs, rhs)
            self.assembler.mov(result, eax)
            self.assembler.add_(end)

            self.frame.pop()
            self.frame.pop()
            self.frame.push('unknown', result)

    def op_lt(self, node):
        self.compile_node(node[0])
        self.compile_node(node[1])

        rhs = self.frame.peek(-1)
        lhs = self.frame.peek(-2)

        if lhs.is_constant() and rhs.is_constant():
            matches = self.rt.relational(lhs.to_boxed_int(), rhs.to_boxed_int(), node.type.lower())

            self.frame.pop()
            self.frame.pop()

            if matches is None:
                self.frame.push_bool(False)
            else:
                self.frame.push_bool(matches)

            return

        @function(c_int, Value, Value)
        def lt(lhs, rhs):
            matches = self.rt.relational(lhs, rhs, True)
            if matches is None:
                return 0
            else:
                return int(matches)

        self.call(lt, lhs, rhs)

        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)

        self.frame.pop()
        self.frame.pop()
        self.frame.push('bool', reg)

    def op_eq(self, node):
        self.equality(node, True)

    def op_ne(self, node):
        self.equality(node, False)

    def equality(self, node, cond):
        self.compile_node(node[0])
        self.compile_node(node[1])

        rhs = self.frame.peek(-1)
        lhs = self.frame.peek(-2)

        if lhs.is_constant() and rhs.is_constant():
            equal = self.rt.equality(lhs.to_boxed_int(), rhs.to_boxed_int())

            self.frame.pop()
            self.frame.pop()

            if equal:
                self.frame.push_bool(cond)
            else:
                self.frame.push_bool(not cond)
        elif (lhs.is_int() or lhs.is_bool()) and (rhs.is_int() or rhs.is_bool()):
            end = Label('end')
            equal = Label('equal')

            reg1 = rhs.to_reg()
            reg2 = lhs.to_reg()

            self.assembler.cmp(reg1, reg2)
            self.assembler.je(equal)
            self.assembler.mov(reg1, int(not cond))
            self.assembler.jmp(end)
            self.assembler.add_(equal)
            self.assembler.mov(reg1, int(cond))
            self.assembler.add_(end)

            self.frame.pop()
            self.frame.pop()
            self.frame.take_reg(reg1)
            self.frame.push('bool', reg1)
        else:
            @function(c_int, BoxedInt, BoxedInt)
            def eq(lhs, rhs):
                print 'stub eq'
                return cond if self.rt.equality(lhs, rhs) else not cond

            emit_inline_path = False
            types = ['int', 'unknown']
            reg = self.frame.alloc_reg()
            stub = Label('stub')
            end = Label('end')

            if rhs.type in types and lhs.type in types:
                reg1 = reg2 = None
                not_equal = Label('not equal')

                if rhs.is_unknown():
                    reg1 = rhs.to_reg()
                    self.jump_not_int(reg1, stub)
                elif not rhs.is_constant():
                    reg1 = rhs.to_reg()

                if lhs.is_unknown():
                    reg2 = lhs.to_reg()
                    self.jump_not_int(reg2, stub)
                elif not rhs.is_constant():
                    reg2 = lhs.to_reg()

                if reg1 is not None and reg2 is not None:
                    self.assembler.mov(reg, reg1)
                    self.assembler.cmp(reg, reg2)

                if reg1 is None:
                    assert isinstance(rhs.value, int)
                    self.assembler.mov(reg, rhs.value << 1)
                    self.assembler.cmp(reg, reg2)

                if reg2 is None:
                    assert isinstance(lhs.value, int)
                    self.assembler.mov(reg, lhs.value << 1)
                    self.assembler.cmp(reg, reg1)

                self.assembler.mov(reg, int(cond))
                self.assembler.je(end)
                self.assembler.mov(reg, int(not cond))
                self.assembler.jmp(end)


            self.assembler.add_(stub)
            self.call(eq, lhs, rhs)
            self.assembler.mov(reg, eax)
            self.assembler.add_(end)

            self.frame.pop()
            self.frame.pop()
            self.frame.push('bool', reg)


    def conditional(self, cond_node, if_node, else_node, if_jump=None, else_jump=None):
        self.compile_node(cond_node)
        self.frame.spill_all(forget=True)

        if_part = Label('if part')
        else_part = Label('else part')
        end = Label('end')

        cond = self.frame.peek(-1)
        if cond.is_constant():
            boolean = self.rt.toBoolean(cond.to_boxed_int())

            if boolean.toBool() == True:
                if if_jump:
                    self.assembler.jmp(if_jump)
                else:
                    self.compile_node(if_node)
            else:
                if else_jump:
                    self.assembler.jmp(else_jump)
                elif else_node:
                    self.compile_node(else_node)
            return
        else:
            @function(c_int, Value)
            def stub_conditional(condition):
                print 'stub conditional'
                return self.rt.toBoolean(condition).raw

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
        if if_node:
            self.assembler.add_(if_part)
            self.compile_node(if_node)
            self.assembler.add_(end)
        else:
            self.assembler.add_(if_part)
            self.assembler.jmp(if_jump)

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
        else:
            self.spill_all(forget=True)
            self.compile_node(node.update)

        if node.update:
            self.compile_node(node.update)
            self.frame.pop()

        self.assembler.jmp(start)
        self.assembler.add_(end)

    def op_while(self, node):

        start = Label('start')
        end = Label('end')
        self.assembler.add_(start)

        if node.condition:
            self.conditional(node.condition, node.body, None, else_jump=end)
        else:
            self.spill_all(forget=True)
            self.compile_node(node.body)

        self.assembler.jmp(start)
        self.assembler.add_(end)

    def op_do(self, node):

        start = Label('start')
        self.assembler.add_(start)

        self.frame.spill_all(forget=True)
        self.compile_node(node.body)

        self.conditional(node.condition, None, None, if_jump=start)

    def op_increment(self, node):
        type = node[0].type.lower()

        if type == 'identifier':
            self.increment_identifier(node, 1)

    def op_decrement(self, node):
        type = node[0].type.lower()

        if type == 'identifier':
            self.increment_identifier(node, -1)

    def increment_identifier(self, node, amount):
        self.op_identifier(node[0])
        if hasattr(node, 'postfix'):
            self.op_identifier(node[0]) # todo this should be self.frame.duplicate or simliar

        self.frame.push_int(1)

        class Nop:
            type = 'nop'

        if amount > 0:
            self.op_plus({
                0 : Nop,
                1 : Nop
            })
        else:
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
        elif type == 'dot':
            self.assign_dot(node)
        else:
            raise Exception('invalid left hand side')


    def op_var(self, nodes):
        for node in nodes:
            if not hasattr(node, 'initializer'):
                continue

            name = node.name

            obj = self.ctx.object
            shape = obj.getShape()

            while True:
                if shape.name == name:
                    slot = shape.slot
                    break

                if shape.next:
                    shape = shape.next[0]
                else:
                    raise Exception('var not found')

            self.compile_node(node.initializer)
            rhs = self.frame.peek(-1)

            self.assembler.mov(self.frame.scratch, obj.pointer)
            self.assembler.mov(self.frame.scratch, self.frame.scratch.addr + 4)
            self.box(rhs, self.frame.scratch.addr + slot * 4)

            self.frame.pop()

    def assign_identifier(self, node):
        self.compile_node(node[1])
        name = node[0].value

        @function(c_int, Value)
        def assign(value):
            self.ctx.object.setProperty(name, value)
            return value.raw

        rhs = self.frame.peek(-1)

        self.call(assign, rhs)
        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)

        self.frame.pop()
        self.frame.push('unknown', reg) # todo: we know the type

    def assign_index(self, node):
        self.compile_node(node[0][0])
        self.compile_node(node[0][1])
        self.compile_node(node[1])

        value = self.frame.peek(-1)
        index = self.frame.peek(-2)
        obj   = self.frame.peek(-3)


        @function(c_int, Value, Value, Value)
        def index_stub(base, index, v):
            assert base.isObject()
            obj = base.toObject()

            name = self.rt.toString(index)
            str = name.toObject().toString()

            obj.setProperty(str, v)

            return v.raw

        self.call(index_stub, obj, index, value)
        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)

        self.frame.pop()
        self.frame.pop()
        self.frame.pop()
        self.frame.push('unknown', reg)

    def assign_dot(self, node):
        self.compile_node(node[0][0])
        self.compile_node(node[1])

        name = node[0][1].value

        value = self.frame.peek(-1)
        obj = self.frame.peek(-2)

        @function(c_int, Value, Value)
        def dot_stub(base,  v):
            assert base.isObject()
            obj = base.toObject()

            obj.setProperty(name, v)

            return v.raw

        self.call(dot_stub, obj, value)
        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)

        self.frame.pop()
        self.frame.pop()
        self.frame.push('unknown', reg)


    def op_identifier(self, node):
        name = node.value

        @function(c_int)
        def identifier():
            return self.ctx.object.getProperty(name).raw

        self.call(identifier)
        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)
        self.frame.push('unknown', reg)

    def op_dot(self, node):
        self.compile_node(node[0])
        name = node[1].value

        @function(c_int, Value)
        def dot(base):
            assert base.isObject()
            obj = base.toObject()
            return obj.getProperty(name).raw

        obj = self.frame.peek(-1)
        self.call(dot, obj)
        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)

        self.frame.pop()
        self.frame.push('unknown', reg)

    def op_index(self, node):
        self.compile_node(node[0])
        self.compile_node(node[1])

        @function(c_int, Value, Value)
        def index_stub(base, index):
            assert base.isObject()
            obj = base.toObject()

            name = self.rt.toString(index)
            str = name.toObject().toString()

            return obj.getProperty(str).raw

        obj = self.frame.peek(-2)
        index = self.frame.peek(-1)

        self.call(index_stub, obj, index)
        reg = self.frame.alloc_reg()
        self.assembler.mov(reg, eax)

        self.frame.pop()
        self.frame.push('unknown', reg)


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
            reg = self.frame.alloc_reg()
            self.assembler.mov(reg, eax)
            self.frame.push('string', reg)

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
    context = Context(Context.GLOBAL)
    compiler = Compiler(asm, runtime, context)

    ast = parse(code)

    fptr = compiler.compile(ast)

    import time
    start = time.clock()
    fptr()
    print time.clock() - start

if __name__ == '__main__':
    main()
