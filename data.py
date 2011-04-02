from ctypes import *

class BoxedInt(Structure):
    _fields_ = [("value", c_int)] # Layout: [ value (31 bit) | type (1 bit)]

    def isInteger(self):
        return self.value & 1

    def getInteger(self):
        assert self.isInteger()
        return self.value >> 1

    def setInteger(self, v):
        self.value = (v << 1) | 1

    def isBool(self):
        return not self.isInteger() and (self.value >> 1) <= 1

    def getBool(self):
        assert self.isBool()
        return bool(self.value >> 1)

    def setBool(self, v):
        assert isinstance(v, bool)
        self.value = (v << 1)

    def isNull(self):
        return self.value == null_value

    def setNull(self):
        self.value = null_value

    def isUndefined(self):
        return self.value == undefined_value

    def setUndefined(self):
        self.value = undefined_value

    def isPrimitive(self):
        return self.isInteger() or (self.value >> 1) <= 2

    def isObject(self):
        return (self.value & 1) == 0 and (self.value >> 1) > 2

    def setObject(self, v):
        self.value = (v << 1)

    def getObject(self):
        return Object(self.value >> 1)

    def getPointer(self):
        return self.value >> 1

class Object():
    def __init__(self, ptr):
        self.ptr = ptr
        self.type = cast(ptr, POINTER(BaseObject))[0].type

    def isPrimitive(self):
        return self.type <= object_types['string']

    def isFloat(self):
        return self.type == object_types['float']

    def isString(self):
        return self.type == object_types['string']

    def toPrimitive(self):
        assert self.isPrimitive()

        if self.isFloat():
            return cast(self.ptr, POINTER(PrimitiveFloat))[0].value
        else:
            return cast(self.ptr, POINTER(PrimitiveString))[0].str


    def clas(self):
        shape = cast(self.ptr, POINTER(JavaScriptObject))[0].shape
        clas = cast(shape, POINTER(Shape))[0].clas
        return clas

    def isObject(self):
        return not self.isPrimitive()

    def isArray(self):
        assert self.type > object_types['string']
        return self.clas() == object_classes['array']

    def to(self, object_type):
        return cast(self.ptr, POINTER(object_type))[0]


class BaseObject(Structure):
    _fields_ = [('type', c_int)]  # minor hack here

class PrimitiveFloat(Structure):
    _fields_ = [('shape', c_void_p),
                ('value', c_float)]

class PrimitiveString(Structure):
    _fields_ = [('shape', c_void_p),
                ('str', c_wchar_p)]

class Shape(Structure):
    _fields_ = [('clas', c_int)]

class JavaScriptObject(Structure):
    _fields_ = [('shape', c_void_p),
                ('properties', c_void_p),
                ('elements', c_void_p)]

class ArrayObject(Structure):
    _fields_ = [('shape', c_void_p),
                ('properties', c_void_p),
                ('elements', c_void_p),
                ('length', c_int)]

    def element(self, index):
        return cast(self.elements, POINTER(c_int))[index]

    def setElement(self, index, value):
        cast(self.elements, POINTER(c_int))[index] = value

    def hasElements(self):
        return self.elements != 0

root = [] # todo arg!!!!!!!!!

def new_string(str):
    obj = PrimitiveString(object_types['string'], str)

    root.append(obj)

    return obj

def new_float(float):
    obj = PrimitiveFloat(object_types['float'], float)

    root.append(obj)

    return obj



def new_array(size=0):
    if size == 0:
        elements = 0
    else:
        ints = create_string_buffer(0x4 * size)
        root.append(ints)
        elements = addressof(ints)

    shape = new_shape(object_classes['array'])
    root.append(shape)

    obj = ArrayObject(addressof(shape), 0, elements, size)
    return obj

def new_shape(clas):
    obj = Shape(clas)
    return obj

def integer_value(int):
    return boxed_integer(int).value

def boxed_integer(int):
    b = BoxedInt()
    b.setInteger(int)
    return b

def object_value(obj):
    return boxed_object(obj).value

def boxed_object(obj):
    b = BoxedInt()
    if isinstance(obj, Structure):
        b.setObject(addressof(obj))
    else:
        b.setObject(obj)
    return b

def bool_value(bool):
    return boxed_bool(bool).value

def boxed_bool(boolean):
    b = BoxedInt()
    b.setBool(bool(boolean))
    return b

object_types = dict(
    # primitives
    float = 1,
    int = 2,
    string = 3,
    # everything higher is object
)

object_classes = dict(
    object = 1,
    array = 2
)

types = dict(
    int = 0,
    float = 1,
    bool = 2,
    null = 3,
    string = 4,
    object = 5,
    unknown = 17
)

false_value = object_value(0)
true_value  = object_value(1)
null_value  = object_value(2)
undefined_value  = object_value(3)


def dump_boxed_int(b):
    if b.isPrimitive():
        if b.isNull():
            print '[null]'
        elif b.isBool():
            print '[true]' if b.getBool() else '[false]'
        else:
            print '[integer] ', b.getInteger()
    else:
        print '[heap object] @', hex(b.getPointer())

        obj = b.getObject()
        if obj.isPrimitive():
            if obj.isString():
                print '[string] ', obj.toPrimitive()
            else:
                print '[float] ', obj.toPrimitive()
        else:
            if obj.isArray():
                obj = obj.to(ArrayObject)
                print '[array] length:', obj.length
                elements = cast(obj.elements, POINTER(c_int))
                for i in range(obj.length):
                    dump_boxed_int(BoxedInt(elements[i]))


