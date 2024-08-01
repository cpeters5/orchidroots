import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_str
from django.utils.functional import Promise

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_str(obj)
        return super().default(obj)

class LazyJSONSerializer:
    def dumps(self, obj):
        return json.dumps(obj, cls=LazyEncoder)

    def loads(self, data):
        return json.loads(data)