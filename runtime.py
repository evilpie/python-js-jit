from data import *

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
        'NaN': new_float(float('nan'))
    }


    def typeof(self, v):
        assert isinstance(v, BoxedInt)

        if v.isInteger():
            return self.strings['number']
        elif v.isPrimitive():
            if v.isNull():
                return self.strings['object']
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
            return object_value(self.floats['NaN'])
        if v.isNull():
            return integer_value(0)
        if v.isBool():
            return integer_value(0 + v.getBool())
        if v.isInteger():
            return v
        obj = v.getObject()
        if obj.isString():
            str = obj.to(PrimitiveString).str
            try:
                v = int(str)
                return integer_value(v)
            except:
                try:
                    v = float(str)
                    return object_value(new_float(v))
                except:
                    return object_value(self.floats['NaN'])

        if obj.isFloat():
            return v

        primitive_value = self.toPrimitive(v, 'number')
        return self.toNumber(primitive_value)


    def toBoolean(self, v):
        if v.isUndefined():
            return BoxedInt(false_value)
        if v.isNull():
            return BoxedInt(false_value)
        if v.isBool():
            return v
        if v.isInteger():
            return v != 0

        obj = v.getObject()
        if obj.isObject():
            return BoxedInt(true_value)
        if obj.isString():
            if len(obj.to(PrimitiveString).str):
                return BoxedInt(true_value)
            return BoxedInt(false_value)

        assert obj.isFloat()
        if bool(obj.to(PrimitiveFloat).value):
            return BoxedInt(true_value)
        return BoxedInt(false_value)



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
                return self.numberConvert(lvalue) == self.numberConvert(rvalue)

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













