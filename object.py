from ctypes import *

root = []

class Object:
    pointer = 0

    primitiveTypes = dict(
        double = 0,
        string = 2
    )

    def __init__(self, pointer):
        self.pointer = pointer

    def isPrimitive(self):
        return self.getType() <= Object.primitiveTypes['string']

    def isString(self):
        return self.getType() == Object.primitiveTypes['string']

    def isDouble(self):
        return self.getType() == Object.primitiveTypes['double']

    def toDouble(self):
        assert self.getType() == Object.primitiveTypes['double']
        return cast(self.pointer, POINTER(PrimitiveDouble_))[0].value

    def toString(self):
        assert self.getType() == Object.primitiveTypes['string']
        return cast(self.pointer, POINTER(PrimitiveString_))[0].value

    def getType(self):
        return cast(self.pointer, POINTER(c_int))[0]

    def getClass(self):
        """ Get the objects class, this fails for primitives """
        pass

    def getClassName(self):
        return self.getShape().clas

    def getShape(self):
        return cast(self.getType(), POINTER(Shape))[0]

    def getProto(self):
        shape = self.getShape()
        return Object(shape.proto)

    def toPlain_(self):
        return cast(self.pointer, POINTER(PlainObject))[0]

    def getProperties(self):
        obj = self.toPlain_()
        return obj.properties

    def getElements(self):
        obj = self.toPlain_()
        return obj.elements

    def getProperty(self, name):
        shape = self.getShape()

        while True:
            if shape.name == name:
                slot = shape.slot
                props = self.getProperties()
                return Value(props[slot])

            if not shape.next:
                return Value(Value.undefined)
            shape = shape.next[0]

        assert False

    def setProperty(self, name, value):
        shape = self.getShape()

        while True:
            if shape.name == name:
                slot = shape.slot
                self.getProperties()[slot] = value.raw
                return

            if not shape.next:
                break
            shape = shape.next[0]

        self.addProperty(name, value)



    def addProperty(self, name, value):
        shape = self.getShape()
        used_slots = []

        while True:
            used_slots.append(shape.slot)
            if not shape.next:
                break

            shape = shape.next[0]

        capacity = self.getShape().capacity
        if len(used_slots) == capacity:
            raise ValueError('can not add new property')

        free = list(set(range(0, capacity)) - set(used_slots))[0]

        new = Shape(0, 0, 0, name, free, 0, 0, None)
        shape.next = pointer(new)

        root.append(new)

        self.getProperties()[free] = value.raw

    def getElement(self, index):
        shape = self.getShape()
        assert index < shape.length

        elements = self.getElements()
        return Value(elements[index])


class Shape(Structure):
    pass

Shape._fields_ = [('type', c_int),
                  ('clas', c_wchar_p),
                  ('proto', c_void_p),
                  ('name', c_wchar_p),
                  ('slot', c_int),
                  ('length', c_int),
                  ('capacity', c_int),
                  ('next',  POINTER(Shape))]

class PrimitiveDouble_(Structure):
    _fields_ = [('type', c_int),
                ('pad_', c_int),
                ('value', c_double)]

class PrimitiveString_(Structure):
    _fields_ = [('type', c_int),
                ('value', c_wchar_p)]


class PlainObject(Structure):
    _fields_ = [('shape', c_void_p),
               ('properties', POINTER(c_int)),
               ('elements', POINTER(c_int))]


class ObjectFactory:

    classes = {
        'plain': 1,
        'array': 2,
        'global': 3
    }

    @staticmethod
    def createPlain(length = None, capacity = None):
        capacity = int(capacity)
        length = int(length)

        new = Shape(ObjectFactory.classes['plain'], 'Object', None, "", -1, length, capacity, None)

        properties = (c_int * capacity)()
        elements = (c_int * length)()


        obj = PlainObject(addressof(new), properties, elements)

        root.append(new)
        root.append(elements)
        root.append(properties)
        root.append(obj)

        return Object(addressof(obj))

    @staticmethod
    def createArray(length = 3):
        length = int(length)

        new = Shape(ObjectFactory.classes['array'], 'Array', None, "", -1, length, 0, None)

        elements = (c_int * length)()

        obj = PlainObject(addressof(new), None, elements)

        root.append(new)
        root.append(elements)
        root.append(obj)

        return Object(addressof(obj))


class Value(Structure):
    _fields_ = [('raw', c_int)]

    pointer = None
    integer = None

    INTEGER_TAG = 0
    POINTER_TAG = 1
    TAG_SIZE = 1


    false     = (0 << TAG_SIZE) | POINTER_TAG
    true      = (1 << TAG_SIZE) | POINTER_TAG
    null      = (2 << TAG_SIZE) | POINTER_TAG
    undefined = (3 << TAG_SIZE) | POINTER_TAG
    hole      = (4 << TAG_SIZE) | POINTER_TAG

    def __init__(self, raw = 0):
        self.raw = raw

    @staticmethod
    def testIntegerFits(value):
        assert isinstance(value, int)

    @staticmethod
    def int(value):
        return Value(value << 1)

    @staticmethod
    def object(pointer):
        return Value((addressof(pointer) << 1) | 1)

    @staticmethod
    def boolean(value):
        self.raw = Value.true if value else Value.false

    def isInt(self):
        return not bool(self.raw & 1)

    def isPointer(self):
        return bool(self.raw & 1)

    def isObject(self):
        return self.isPointer() and not self.isSpecial()

    def isSpecial(self):
        return (self.raw & 1) and self.raw <= Value.hole

    def isBoolean(self):
        return self.raw == Value.true or self.raw == Value.false

    def isNull(self):
        return self.raw == Value.null

    def isUndefined(self):
        return self.raw == Value.undefined

    def isHole(self):
        return self.raw == Value.hole

    def toInt(self):
        return self.raw >> 1

    def toPointer(self):
        return self.raw >> 1

    def toObject(self):
        return Object(self.raw >> 1)

    def setBoolean(self, boolean):
        self.raw = Value.true if boolean else Value.false

    def setNull(self):
        self.raw = Value.null

    def setUndefined(self):
        self.raw = Value.undefined

    def dump(self):
        if self.isSpecial():
            if self.isBoolean():
                print '[Boolean] %s' % self.toBoolean()
            if self.isNull():
                print '[Null]'
            if self.isUndefined():
                print '[Undefined]'
            if self.isHole():
                print '[Hole]'

        elif self.isInt():
            print '[Int] %d' % self.toInt()
        else:
            obj = self.toObject()
            print '[Heap Object] @ %X' % obj.pointer

            if obj.isString():
                print '   [String] "%s"' % obj.toString()
            elif obj.isDouble():
                print '   [Double] %f' % obj.toDouble()
            else:
                print '   [%s]' % obj.getClassName()

                shape = obj.getShape()
                while True:
                    if shape.name:
                        print '       %s: %d' % (shape.name, obj.getProperties()[shape.slot])

                    if shape.next:
                        shape = shape.next[0]
                    else:
                        break

                for i in range(0, shape.length):
                    print '       %d: %d' % (i, obj.getElements()[i])

class Error:
    pass


