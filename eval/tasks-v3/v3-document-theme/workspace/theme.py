import hashlib

def stable_name(url: str) -> str:
    return 'r-'+hashlib.sha256(url.encode()).hexdigest()[:12]+'.bin'

def resolve(tree: dict, rules: list[dict]) -> dict:
    return {**tree, 'style': {'color':'black','font':'serif','margin':0,'display':'block'},'resource':stable_name(tree['resource']) if 'resource' in tree else None,'children':[resolve(c,rules) for c in tree.get('children',[])]}

def resources(tree: dict) -> dict:
    result={}
    if 'resource' in tree:
        result[stable_name(tree['resource'])]=tree['resource']
    for child in tree.get('children',[]):
        result.update(resources(child))
    return result
