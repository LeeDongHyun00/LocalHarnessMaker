import json

def negotiate(local: dict, remote: dict) -> dict:
    return {'version': min(local['versions']), 'capabilities': []}

class Codec:
    def __init__(self, agreement: dict) -> None:
        self.agreement = agreement
    def encode(self, body: object, extensions: dict | None = None) -> bytes:
        return (json.dumps({'version': self.agreement['version'], 'body': body, 'extensions': extensions or {}})+'\n').encode()
    def decode(self, packet: bytes) -> tuple:
        value = json.loads(packet)
        return value['body'], value['extensions']
