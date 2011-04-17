from data import *
import math
from object import Value, Object

ecma_type = dict(undefined = 0, null = 1, boolean = 2, string = 3, number = 4, object = 5)

class Runtime:
    strings = {
        'boolean': new_string('boolean'),
        'number': new_string('number'),
        'object': new_string('object'),
        'string': new_string('string'),
        'null': new_string('null'),
        'undefined': new_string('undefined'),
        'true': new_string('true'),
        'false': new_string('false'),
    }

    doubles = {
        'NaN': new_double(float('nan')),
        'negative_zero': new_double(float('-0.0'))
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
            obj = v.toObject()
            if obj.isPrimitive():
                if obj.isString():
                    return self.strings['string']
                else:
                    return self.strings['number']

            return self.strings['object'] # todo fix for "function"

    def type(self, v):
        if v.isInt():
            return ecma_type['number']
        if v.isBoolean():
            return ecma_type['boolean']
        if v.isNull():
            return ecma_type['null']
        if v.isUndefined():
            return ecma_type['undefined']

        obj = v.toObject()
        if obj.isDouble():
            return ecma_type['number']
        if obj.isString():
            return ecma_type['string']

        return ecma_type['object']

    def numberConvert(self, v):
        if v.isInt():
            return v.toInt()
        if v.isObject():
            obj = v.toObject()
            assert obj.isDouble()

            return obj.toDouble()
        assert False

    def toNumber(self, v):
        if v.isUndefined():
            return Value.object(self.doubles['NaN'])
        if v.isNull():
            return Value.int(0)
        if v.isBoolean():
            return Value.int(0 + v.toBoolean())
        if v.isInt():
            return v
        obj = v.toObject()
        if obj.isString():
            str = obj.toString()
            try:
                v = int(str)
                return Value.int(v)
            except:
                try:
                    v = float(str)
                    return Value.object(new_float(v))
                except:
                    return Value.object(self.doubles['NaN'])

        if obj.isDouble():
            return v

        primitive_value = self.toPrimitive(v, 'number')
        return self.toNumber(primitive_value)


    def toBoolean(self, v):
        if v.isUndefined():
            return Value(Value.false)
        if v.isNull():
            return Value(Value.false)
        if v.isBoolean():
            return v
        if v.isInt():
            return Value.boolean(v.toInt())

        obj = v.toObject()
        if obj.isObject():
            return Value(Value.true)
        if obj.isString():
            return Value.boolean(obj.toString())

        assert obj.isDouble()
        double = obj.toDouble()
        if math.isnan(double):
            return Value(Value.false)
        return Value.boolean(double)

    def toString(self, v):
        if v.isUndefined():
            return Value.object(self.strings['undefined'])
        if v.isNull():
            return Value.object(self.strings['null'])
        if v.isBoolean():
            return Value.object(self.strings['true'] if v.toBoolean() else self.strings['false'])
        if v.isInt():
            return Value.object(new_string(str(v.toInt())))

        assert v.isObject()
        obj = v.toObject()
        if obj.isPrimitive():
            if obj.isDouble():
                return Value.object(new_string(obj.toString()))
            else:
                return v

        raise NotImplementedError('js object to string')

    def toPrimitive(self, v, hint=None):
        if not v.isObject():
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
                lvalue = left.toObject().to(PrimitiveString).str
                rvalue = right.toObject().to(PrimitiveString).str
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
            lvalue = left.toObject().to(PrimitiveString).str
            rvalue = right.toObject().to(PrimitiveString).str
            return lvalue == rvalue

        lvalue = self.toNumber(left)
        rvalue = self.toNumber(right)
        return self.numberConvert(lvalue) == self.numberConvert(rvalue)

    def relational(self, left, right, left_first = True):
        if left_first:
            px = self.toPrimitive(left, 'number')
            py = self.toPrimitive(right, 'number')
        else:
            py = self.toPrimitive(right, 'number')
            px = self.toPrimitive(left, 'number')

        if not (self.type(px) == self.type(py) == ecma_type['string']):
            nx = self.toNumber(px)
            ny = self.toNumber(py)

            vx = self.numberConvert(nx)
            vy = self.numberConvert(ny)

            if math.isnan(vx) or math.isnan(vy):
                return None

            if vx == vy:
                return False

            # todo step f. - k.

            return vx < vy

        if px.startswith(py):
            return False

        if py.startswith(px):
            return True

        return px < py

    def add(self, left, right):
        left = self.toPrimitive(left)
        right = self.toPrimitive(right)

        ltype = self.type(left)
        rtype = self.type(right)
        if ltype == ecma_type['string'] or rtype == ecma_type['string']:
            left = self.toString(left)
            right = self.toString(right)

            lstr = left.toObject().toString()
            rstr = right.toObject().toString()

            return Value.object(new_string(lstr + rstr))


        left = self.toNumber(left)
        right = self.toNumber(right)

        number = self.numberConvert(left) + self.numberConvert(right)
        return Value(boxed_number(number).value)

    def sub(self, left, right):
        left = self.toNumber(left)
        right = self.toNumber(right)

        number = self.numberConvert(left) - self.numberConvert(right)
        return boxed_number(number)
