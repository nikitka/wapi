from wapi.exceptions import ApiError
from wapi.serializers.decorators import *

SERIALIZERS_REGISTRY = {}

class Serialization(object):
    def __init__(self, name, method):
        self.name = name
        self.method = method
    
    def apply(self, obj, **kwargs):
        return (self.name, self.method(obj, **kwargs))


class NoSerializationMethod(RuntimeError):
    pass

class BaseSerializerType(type):
    def __init__(mcs, name, bases, dct):
        super(BaseSerializerType, mcs).__init__(name, bases, dct)
        if hasattr(mcs, 'serializes'):
            SERIALIZERS_REGISTRY[mcs.serializes] = mcs()
            
class BaseSerializer(object):
    obj_names = {}
    def __init__(self, *args, **kwargs):
        super(BaseSerializer, self).__init__(*args, **kwargs)
        for k, v in self.__class__.__dict__.iteritems():
            if hasattr(v, 'obj_name'):
                self.__class__.obj_names[v] = v.obj_name

    def obj_name(self, func):
        return self.__class__.obj_names.get(func)

    def default(self, obj, **kw):
        try:
            return dict([(k, v) for k, v in obj.__dict__.iteritems() if not k.startswith('_')])
        except AttributeError:
            return dict()

    def _get_serialization(self, obj, method):
        try:
            m = getattr(self, method or 'default')
        except AttributeError:
            raise NoSerializationMethod('Serialization "%s" is not defined in serializer "%s" for object "%s"' % \
                (method, SERIALIZERS_REGISTRY.get(obj.__class__, Serializer).__name__, obj.__class__.__name__))
        return Serialization(self.obj_name(m) or obj.__class__.__name__.lower(), m)

    def _do_serialization(self, obj, method=None, **kw):
        serialization = self._get_serialization(obj, method)
        return serialization.apply(obj, **kw)

class Serializer(BaseSerializer):
    __metaclass__ = BaseSerializerType

class DictSerializer(Serializer):
    serializes = {}.__class__

    def default(self, obj, **kwargs):
        from wapi.serializers import chain
        result = {}
        for k, v in obj.iteritems():
            result[k] = chain(v)
            """FIXME 

               The reason for the check: {'test': 1} would generate
               <dict><test><int /></test></dict> with chaining.
               
               Another 'possible' fix is to modify l:114 to return obj
               instead of dict() which would result in
               <dict><test><int>1</int></test></dict>"""
            if result[k] is None or (len(result[k]) == 1 and \
               (result[k].items()[0][1] is None or \
               len(result[k].items()[0][1]) == 0)):
                result[k] = v
        return result

class ApiErrorSerializer(Serializer):
    serializes = ApiError

    @objname('error')
    def default(self, obj, **kwargs):
        return {'message': obj.message, 'type': obj.__class__.__name__, 'status_code': obj.status_code}

DEFAULT_SERIALIZER = Serializer()
