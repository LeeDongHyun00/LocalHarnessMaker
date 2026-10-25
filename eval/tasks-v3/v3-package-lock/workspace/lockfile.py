from versions import version_tuple
import json

def resolve(requirements: dict, candidates: list[dict], allow_prerelease: bool = False) -> bytes:
    rows=[]
    for name in sorted(requirements):
        matches=[c for c in candidates if c['name']==name]
        if not matches:
            raise ValueError('unresolved:'+name)
        rows.append(matches[0])
    return (json.dumps({'packages':rows},sort_keys=True,separators=(',',':'))+'\n').encode().replace(b'\\n',b'\n')
