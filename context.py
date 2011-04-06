from object import Object, PlainObject, Value, Shape
from ctypes import c_int, addressof

class Context:
    GLOBAL = 0
    FUNCTION = 1

    def __init__(self, type, scope = None):
        self.type = type
        self.scope = scope
        self.object = None
        self.this = None

        if type == Context.GLOBAL:
            self.setupGlobal()

    def setupGlobal(self):
        self.scope = None

        global_shape = Shape(0xf, 'Global', None, "", -1, 0, 0xff, None)
        global_properties = (c_int * 0xff)()
        global_object = PlainObject(addressof(global_shape), global_properties, None)

        self.root = [global_shape, global_properties, global_object]

        obj = Object(addressof(global_object))
        self.this = obj
        self.object = obj





