class QueryError(ValueError): pass
def parse(source: str) -> dict:
    return {'type':'word','value':source,'span':[0,len(source)]}
def plan(ast: dict) -> dict: return {'filters':[],'residual':ast}
def execute(documents: list[dict], query: str) -> dict:
    return {'ids':[d['id'] for d in documents if query.casefold() in d['text'].casefold().split()],'explain':plan(parse(query))}
def search(documents: list[dict], request: str | dict) -> list:
    return execute(documents,request if isinstance(request,str) else request['term'])['ids']
