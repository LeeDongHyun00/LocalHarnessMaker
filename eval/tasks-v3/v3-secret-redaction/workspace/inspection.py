import json

def inspect_config(data: object, secret_fields: object) -> list[dict]:
    return [{'path':'','value':data,'secret':False}]

def dump_config(data: object, secret_fields: object) -> str:
    return json.dumps(inspect_config(data,secret_fields),sort_keys=True,separators=(',',':'))
