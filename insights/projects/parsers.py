import json

from django.core.serializers.json import DjangoJSONEncoder


def parse_dict_to_json(data):
    return json.dumps(data, cls=DjangoJSONEncoder)
