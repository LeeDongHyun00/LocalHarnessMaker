import ast
from typing import Any
class ExtractError(ValueError): pass
def extract(sources: dict[str, str]) -> list[dict]:
    result=[]
    for filename,source in sources.items():
        for node in ast.walk(ast.parse(source)):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='_':
                result.append({'id':node.args[0].value,'comments':[],'locations':[]})
    return result
