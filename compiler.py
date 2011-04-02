from ctypes import *

from pyasm import Program, Label
import pyasm.instructions
from pyasm.instructions import *
from pyasm.registers import al, ah, eax, esp, ebp, ebx, edx, ecx, xmm0, xmm1
from pyasm.base import Address
from pyasm.data import function, String

from jsparser import parse

from struct import *
from data import *

class Frame:
    def __init__(self, assembler):
        self.assembler = assembler
        self.last = None
        self.stack = []

    def push(self, type, register):
        self.assembler.push(register)
        self.stack.append(type)

    def pop(self, register):
        self.assembler.pop(register)
        return self.stack.pop()

    def peek(self, index):
        return self.stack[index]


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

        self.assembler.push(ebp)
        self.assembler.mov(ebp, esp)

        self.op_block(ast)

        self.assembler.pop(ebp)
        self.assembler.ret()

        print self.assembler.assembler

        return self.assembler.compile()

    def compile_node(self, node):
        getattr(self, 'op_' + node.type.lower())(node)

    def box(self, type, register):
        if type == 'unknown':
            pass # already boxed
        else:
            if type == 'int':
                self.assembler.shl(register, 1)
            else:
                self.assembler.shl(register, 1)
                self.assembler.add(register, 1)

    def unbox(self, register):
        self.assembler.sar(register, 1)

    def jump_not_int(self, register, jump):
        self.assembler.test(register, 1)
        self.assembler.jnz(jump)

    def op_comma(self, nodes):
        for node in nodes[:-1]:
            self.compile_node(node)
            self.frame.pop(eax)

        self.compile_node(nodes[-1])

    def op_block(self, nodes):
        t = None
        for node in nodes:
            self.compile_node(node)

    def op_group(self, node):
        self.compile_node(node[0])

    def op_semicolon(self, node):
        self.compile_node(node.expression)

        type = self.frame.pop(eax)
        self.box(type, eax)
        self.assembler.mov(ebx, addressof(self.return_value))
        self.assembler.mov(ebx.addr + 0, eax)

    def op_number(self, node):
        value = node.value

        if isinstance(value, int):
            self.frame.push('int', value)
        else:
            double = new_double(value)
            self.constant_pool.append(double)
            self.frame.push('double', addressof(double))

    def op_string(self, node):
        value = node.value

        str = new_string(value)
        self.constant_pool.append(str)
        self.frame.push('string', addressof(str))

    def op_array_init(self, nodes):
        for node in nodes:
            if node: # could be hole
                self.compile_node(node)

        @function(c_int, c_int)
        def array_init(size):
            print 'stub array init', size

            obj = new_array(size)
            self.constant_pool.append(obj)

            return addressof(obj)

        self.assembler.push(len(nodes)) #size
        self.assembler.mov(eax, array_init)
        self.assembler.call(eax)
        self.assembler.add(esp, 4)

        self.assembler.mov(ebx, eax.addr + 8) # elements

        i = (len(nodes) - 1) * 4
        for node in nodes:
            if node:
                t = self.frame.pop(ecx)
                self.box(t, ecx)
                self.assembler.mov(ebx.addr + i, ecx)
            else:
                self.assembler.mov(ebx.addr + i, undefined_value) # todo: needs special value
            i = i - 4

        self.frame.push('object', eax)


    def op_unary_minus(self, node):
        self.compile_node(node[0])

        lhs = self.frame.pop(eax)
        if lhs == 'int':
            self.assembler.neg(eax)
            self.frame.push('int', eax)
        elif lhs == 'double':

            self.assembler.bytes(0x0f, 0x10, 0x00)          #movups xmm0, [eax]
            self.assembler.pxor(xmm1, xmm1)                 #pxor xmm1, xmm1
            self.assembler.bytes(0x66, 0x0f, 0x5c, 0xc8)    #subpd xmm1, xmm0
            self.assembler.bytes(0x0f, 0x11, 0x08)          #movups [eax], xmm1

            self.frame.push('double', eax)
        elif lhs == 'null':
            self.frame.push('double', addressof(self.rt.doubles['negative_zero']))
        elif lhs == 'undefined':
            self.frame.push('double', addressof(self.rt.doubles['NaN']))
        else:

            self.box(lhs, eax)

            @function(c_int, BoxedInt)
            def unary_minus(lhs):
                return self.rt.sub(boxed_integer(0), lhs).value

            self.box(lhs, eax)
            self.assembler.push(eax)
            self.assembler.mov(eax, unary_minus)
            self.assembler.call(eax)
            self.assembler.add(esp, 4)

            self.frame.push('unknown', eax)

    def op_unary_plus(self, node):
        self.compile_node(node[0])

        lhs = self.frame.peek(-1)
        if lhs in ['int', 'double']:
            return # nothing to do here

        lhs = self.frame.pop(eax)
        if lhs == 'bool':
            self.frame.push('int', eax) # true is 1 and false is 0 already
        elif lhs == 'null':
            self.frame.push('int', 0)
        elif lhs == 'undefined':
            self.frame.push('double', addressof(self.rt.doubles['NaN']))
        else:
            @function(c_int, BoxedInt)
            def unary_plus(lhs):
                print 'stub unary plus'
                return self.rt.toNumber(lhs).value

            stub = Label('stub')
            end = Label('end')

            if lhs == 'unknown':
                self.jump_not_int(eax, stub)
                self.assembler.jmp(end) # nothing to do already int

            self.assembler.add_(stub)
            self.box(lhs, eax)
            self.assembler.push(eax)
            self.assembler.mov(eax, unary_plus)
            self.assembler.call(eax)
            self.assembler.add(esp, 4)

            self.assembler.add_(end)
            self.frame.push('unknown', eax)


    def op_not(self, node):
        self.compile_node(node[0])

        lhs = self.frame.pop(eax)
        if lhs == 'bool':
            self.assembler.xor(eax, 1)
            self.frame.push('bool', eax)
        elif lhs == 'int':
            end = Label('end')

            self.assembler.cmp(eax, 0)
            self.assembler.xor(eax, eax)
            self.assembler.jne(end)
            self.assembler.mov(eax, 1)
            self.assembler.add_(end)

            self.frame.push('bool', eax)
        elif lhs == 'null' or lhs == 'undefined':
            self.frame.push('bool', 1)
        elif lhs == 'object':
            self.frame.push('bool', 0)
        else:

            @function(c_int, BoxedInt)
            def not_(lhs):
                v = self.rt.toBoolean(lhs)
                if v.value == true_value:
                    return 0
                else:
                    return 1

            self.box(lhs, eax)
            self.assembler.push(eax)
            self.assembler.mov(eax, not_)
            self.assembler.call(eax)
            self.assembler.add(esp, 4)

            self.frame.push('bool', eax)

    def op_void(self, node):
        self.compile_node(node[0])

        lhs = self.frame.pop(eax)

        @function(None, BoxedInt)
        def log(v):
            print 'void stub (logging)'
            dump_boxed_int(v)

        self.box(lhs, eax)

        self.assembler.push(eax)
        self.assembler.mov(eax, log)
        self.assembler.call(eax)
        self.assembler.add(esp, 4)

        self.frame.push('undefined', 3)

    def op_plus(self, node):
        self.op_binary(node, 'add')
    def op_minus(self, node):
        self.op_binary(node, 'sub')

    def op_binary(self, node, op):
        self.compile_node(node[0])
        self.compile_node(node[1])

        rhs = self.frame.pop(ebx)
        lhs = self.frame.pop(eax)

        if lhs == rhs == 'int':
            getattr(self.assembler, op)(eax, ebx)
            self.frame.push('int', eax)
            return
        elif lhs == rhs == 'double':
            self.assembler.bytes(0x0f, 0x10, 0x00)          #movups xmm0, [eax]
            self.assembler.bytes(0x0f, 0x10, 0x0b)          #movups xmm1, [ebx]
            getattr(self.assembler, op + 'pd')(xmm1, xmm0)  #subpd xmm1, xmm0
            self.assembler.bytes(0x0f, 0x11, 0x08)          #movups [eax], xmm1

            self.frame.push('double', eax)
            return
        elif lhs in ['int', 'double'] and rhs in ['int', 'double']:
            if lhs == 'int':
                self.assembler.cvtsi2ss(xmm0, eax)
            else:
                self.assembler.bytes(0x0f, 0x10, 0x00) #movups xmm0, [eax]

            if rhs == 'int':
                self.assembler.cvtsi2ss(xmm1, xmm)
            else:
                self.assembler.bytes(0x0f, 0x10, 0x0b) #movups xmm1, [ebx]

            getattr(self.assembler, op + 'pd')(xmm1, xmm0) # select operation

            if lhs == 'double':
                self.assembler.bytes(0x0f, 0x11, 0x08)  #movups [eax], xmm1
                self.frame.push('double', eax)
            else:
                self.assembler.bytes(0x0f, 0x11, 0x0b)  #movups [ebx], xmm1
                self.frame.push('double', ebx)
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

        self.box(rhs, ebx)
        self.box(lhs, eax)

        self.assembler.push(ebx)
        self.assembler.push(eax)
        self.assembler.mov(ecx, stubs[op])
        self.assembler.call(ecx)
        self.assembler.add(esp, 8)

        self.frame.push('unknown', eax)

    def op_true(self, node):
        self.frame.push('bool', 1)

    def op_false(self, node):
        self.frame.push('bool', 0)

    def op_null(self, node):
        self.frame.push('null', 2)

    def op_eq(self, node):
        self.compile_node(node[0])
        self.compile_node(node[1])

        rhs = self.frame.pop(ecx)
        lhs = self.frame.pop(ebx)

        if lhs in ['int', 'bool'] and rhs in ['int', 'bool']:
            end = Label('end')

            self.assembler.mov(eax, 1)
            self.assembler.cmp(ecx, ebx)  # ZF = ~(a & b)
            self.assembler.je(end)        # ZF == 0
            self.assembler.mov(eax, 0)
            self.assembler.add_(end)

            self.frame.push('bool', eax)
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
                print 'stub eq'
                return 1 if self.rt.equality(lhs, rhs) else 0

            stub = Label('stub')
            end = Label('end')
            emit_inline_cmp = False

            if lhs == 'unknown' and rhs in ['int', 'unknown']:
                emit_inline_cmp = True
                self.jump_not_int(ebx, stub)

            if rhs == 'unknown' and lhs in ['int', 'unknown']:
                emit_inline_cmp = True
                self.jump_not_int(ecx, stub)

            if emit_inline_cmp:
                if lhs == 'unknown':
                    self.unbox(ebx)
                if rhs == 'unknown':
                    self.unbox(ecx)
                self.assembler.mov(eax, 1)
                self.assembler.cmp(ecx, ebx)
                self.assembler.je(end)
                self.assembler.mov(eax, 0)
                self.assembler.jmp(end)

            self.assembler.add_(stub)
            self.box(rhs, ecx)
            self.assembler.push(ecx)
            self.box(lhs, ebx)
            self.assembler.push(ebx)
            self.assembler.mov(eax, eq)
            self.assembler.call(eax)
            self.assembler.add(esp, 8)
            self.assembler.add_(end)

            self.frame.push('bool', eax)


    def conditional(self, cond_node, if_node, else_node, else_jump=None):
        self.compile_node(cond_node)

        type = self.frame.pop(eax)

        if_part = Label('if part')
        else_part = Label('else part')
        end = Label('end')

        if type == 'int':
            self.assembler.cmp(eax, 0)
            self.assembler.jne(if_part)
        elif type == 'bool':
            self.assembler.test(eax, 1)
            self.assembler.jne(if_part)
        elif type == 'null':
            pass # always else_node
        elif type == 'object':
            self.assembler.jmp(if_part) # {} ? true : false => always true
        elif type == 'string':
            raise NotImplementedError('str conditional')
        else:

            @function(c_int, BoxedInt)
            def stub_conditional(condition):
                print 'stub conditional'
                return self.rt.toBoolean(condition).value

            test = Label('test')
            stub = Label('stub')

            self.assembler.add_(test)
            self.box(type, eax) # currently only required for double

            #test for bool
            self.assembler.cmp(eax, true_value)
            self.assembler.je(if_part)
            self.assembler.cmp(eax, false_value)
            self.assembler.je(else_part)

            #test for int
            self.jump_not_int(eax, stub)
            self.assembler.cmp(eax, 0)
            self.assembler.jne(if_part)
            self.assembler.jmp(else_part)

            #stub
            self.assembler.add_(stub)
            self.assembler.push(eax)
            self.assembler.mov(ebx, stub_conditional)
            self.assembler.call(ebx)
            self.assembler.add(esp, 4)
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
            self.frame.pop(eax)

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

        if node.postfix:
            type = self.frame.pop(eax)
            self.frame.push(type, eax)
            self.frame.push(type, eax)

        self.frame.push('int', amount)

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

        if node.postfix:
            self.frame.pop(eax)

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
            rhs = self.frame.pop(eax)

            self.box(rhs, eax)
            self.assembler.mov(ebx, addressof(self.var_space))
            self.assembler.mov(ebx.addr + index * 4, eax)

    def assign_identifier(self, node):
        name = node[0].value

        if not name in self.vars:
            raise 'var not declared'

        index = self.vars[name]

        self.compile_node(node[1])
        rhs = self.frame.pop(eax)

        if rhs == 'unknown':
            self.assembler.mov(ebx, addressof(self.var_space))
            self.assembler.mov(ebx.addr + index * 4, eax)

            self.frame.push('unknown', eax)
        else:
            self.assembler.mov(edx, eax)
            self.box(rhs, edx)
            self.assembler.mov(ebx, addressof(self.var_space))
            self.assembler.mov(ebx.addr + index * 4, edx)

            self.frame.push(rhs, eax)

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

        self.assembler.mov(ebx, addressof(self.var_space))
        self.assembler.mov(eax, ebx.addr + index * 4)

        self.frame.push('unknown', eax)

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

        type = self.frame.pop(eax)
        if type == 'int' or type == 'double':
            self.frame.push('string', addressof(self.rt.strings['number']))
        elif type == 'null':
            self.frame.push('string', addressof(self.rt.strings['null']))
        elif type == 'bool':
            self.frame.push('string', addressof(self.rt.strings['boolean']))
        elif type == 'string':
            self.frame.push('string', addressof(self.rt.strings['string']))
        else:
            @function(c_int, BoxedInt)
            def typeof(v):
                str = self.rt.typeof(v)
                return addressof(str)

            self.box(type, eax)
            self.assembler.push(eax)
            self.assembler.mov(ebx, typeof)
            self.assembler.call(ebx)
            self.assembler.add(esp, 4)

            self.frame.push('string', eax)

    def op_nop(self, node):
        pass

def main():
    import sys
    from runtime import Runtime

    file = sys.argv[1]
    code = open(file).read()

    asm = Program()
    runtime = Runtime()
    compiler = Compiler(asm, runtime)

    ast = parse(code)

    raw_input()
    fptr = compiler.compile(ast)
    fptr()

    print ""
    print " === Returned === "
    dump_boxed_int(compiler.return_value)


main()
