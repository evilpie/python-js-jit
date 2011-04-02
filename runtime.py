from data import *
import math

ecma_type = dict(undefined = 0, null = 1, boolean = 2, string = 3, number = 4, object = 5)

class Runtime:
    strings = {
        'boolean': new_string('boolean'),
        'number': new_string('number'),
        'object': new_string('object'),
        'string': new_string('string'),
        'null': new_string('null'),
        'undefined': new_string('undefined')
    }

    floats = {
        'NaN': new_float(float('nan')),
        'negative_zero': new_float(float('-0.0'))
    }


    def typeof(self, v):
        assert isinstance(v, BoxedInt)

        if v.isInteger():
            return self.strings['number']
        elif v.isPrimitive():
            if v.isNull():
                return self.strings['null'] # see http://wiki.ecmascript.org/doku.php?id=proposals:typeof
            elif v.isUndefined():
                return self.strings['undefined']
            elif v.isBool():
                return self.strings['boolean']
        else:
            obj = v.getObject()
            if obj.isPrimitive():
                if obj.isString():
                    return self.strings['string']
                else:
                    return self.strings['number']

            return self.strings['object'] # todo fix for "function"

    def type(self, v):
        if v.isInteger():
            return ecma_type['number']
        if v.isBool():
            return ecma_type['boolean']
        if v.isNull():
            return ecma_type['null']
        if v.isUndefined():
            return ecma_type['undefined']

        obj = v.getObject()
        if obj.isFloat():
            return ecma_type['number']
        if obj.isString():
            return ecma_type['string']

        return ecma_type['object']

    def numberConvert(self, v):
        if v.isInteger():
            return v.getInteger()
        if v.isObject():
            obj = v.getObject()
            assert obj.isFloat()

            return obj.to(PrimitiveFloat).value
        assert False

    def toNumber(self, v):
        if v.isUndefined():
            return boxed_object(self.floats['NaN'])
        if v.isNull():
            return boxed_integer(0)
        if v.isBool():
            return boxed_integer(0 + v.getBool())
        if v.isInteger():
            return v
        obj = v.getObject()
        if obj.isString():
            str = obj.to(PrimitiveString).str
            try:
                v = int(str)
                return boxed_integer(v)
            except:
                try:
                    v = float(str)
                    return boxed_object(new_float(v))
                except:
                    return boxed_object(self.floats['NaN'])

        if obj.isFloat():
            return v

        primitive_value = self.toPrimitive(v, 'number')
        return self.toNumber(primitive_value)


    def toBoolean(self, v):
        if v.isUndefined():
            return boxed_bool(False)
        if v.isNull():
            return boxed_bool(False)
        if v.isBool():
            return v
        if v.isInteger():
            return boxed_bool(v.getInteger())

        obj = v.getObject()
        if obj.isObject():
            return boxed_bool(True)
        if obj.isString():
            if len(obj.to(PrimitiveString).str):
                return boxed_bool(True)
            return boxed_bool(False)

        assert obj.isFloat()
        float_value = obj.to(PrimitiveFloat).value
        if math.isnan(float_value):
            return boxed_bool(False)
        return boxed_bool(float_value)



    def toPrimitive(self, v, hint=None):
        if v.isPrimitive():
            return v
        obj = v.toObject()
        if obj.isPrimitive():
            return v

        return self.defaultValue(obj, hint)

    def defaultValue(self, object, hint):
        assert 'omg how deep are wee', False

    def equality(self, left, right):
        ltype = self.type(left)
        rtype = self.type(right)
        if ltype == rtype:
            if ltype == ecma_type['undefined']:
                return True
            if ltype == ecma_type['null']:
                return True
            if ltype == ecma_type['number']:
                return self.numberConvert(left) == self.numberConvert(right)

            if ltype == ecma_type['string']:
                lvalue = left.getObject().to(PrimitiveString).str
                rvalue = right.getObject().to(PrimitiveString).str
                return lvalue == rvalue

            # either bool or object
            return left.value == right.value

        if ltype == ecma_type['null'] and rtype == ecma_type['undefined']:
            return True

        if ltype == ecma_type['undefined'] and rtype == ecma_type['null']:
            return True

        if ltype == ecma_type['object']:
            pass

        if rtype == ecma_type['object']:
            pass

        if ltype == rtype == ecma_type['string']:
            lvalue = left.getObject().to(PrimitiveString).str
            rvalue = right.getObject().to(PrimitiveString).str
            return lvalue == rvalue

        return self.toNumber(left) == self.toNumber(right)


    def add(self, left, right):
        left = self.toPrimitive(left)
        right = self.toPrimitive(right)

        ltype = self.type(left)
        rtype = self.type(right)
        if ltype == ecma_type['string'] or rtype == ecma_type['string']:
            return boxed_integer(0xdead)

        left = self.toNumber(left)
        right = self.toNumber(right)

        number = self.numberConvert(left) + self.numberConvert(right)
        return boxed_number(number)

    def sub(self, left, right):
        left = self.toNumber(left)
        right = self.toNumber(right)

        number = self.numberConvert(left) - self.numberConvert(right)
        return boxed_number(number)
