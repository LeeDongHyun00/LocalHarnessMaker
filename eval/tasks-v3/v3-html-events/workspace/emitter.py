import html

def render(node: str | tuple) -> str:
    if isinstance(node, str):
        return html.escape(node, quote=False)
    tag, attributes, children = node
    attrs = ''.join(' ' + key + '="' + html.escape(value, quote=True) + '"' for key, value in attributes)
    return '<' + tag + attrs + '>' + ''.join(render(child) for child in children) + '</' + tag + '>'
