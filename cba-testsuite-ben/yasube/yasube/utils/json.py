import json


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return obj.to_json()
        else:
            return json.JSONEncoder.default(self, obj)

    def dump(self):
        # Only callable from direct children
        return json.dumps(self, cls=self.__class__.__base__)
