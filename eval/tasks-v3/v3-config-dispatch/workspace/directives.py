from collections.abc import Callable, Mapping

Handler = Callable[[dict[str, str], str, int], None]

def _pair(argument: str, line: int) -> tuple[str, str]:
    pieces = argument.split(None,1)
    if len(pieces) != 2:
        raise ValueError(f'line {line}: argument')
    return pieces[0],pieces[1]

def _set(state: dict[str,str], argument: str, line: int) -> None:
    key,value = _pair(argument,line)
    state[key] = value

def _unset(state: dict[str,str], argument: str, line: int) -> None:
    if not argument or len(argument.split()) != 1:
        raise ValueError(f'line {line}: argument')
    state.pop(argument,None)

def _append(state: dict[str,str], argument: str, line: int) -> None:
    key,value = _pair(argument,line)
    state[key] = state[key] + ',' + value if key in state else value

class Parser:
    def __init__(self) -> None:
        self.handlers = {'set':_set,'unset':_unset,'append':_append}
    def register(self, name: str, handler: Handler) -> None:
        if not name or not name.isascii() or not name.isalpha() or not name.islower():
            raise ValueError('invalid directive')
        if name in self.handlers:
            raise ValueError('duplicate directive: ' + name)
        self.handlers[name] = handler

    def parse(self, text: str, initial: Mapping[str,str] | None = None) -> dict[str,str]:
        state = dict(initial) if initial is not None else {}
        for number,line in enumerate(text.splitlines(),1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'): continue
            pieces = stripped.split(None,1)
            name = pieces[0]
            argument = pieces[1] if len(pieces) == 2 else ''
            if name == 'set': _set(state,argument,number)
            elif name == 'unset': _unset(state,argument,number)
            elif name == 'append': _append(state,argument,number)
            else: raise ValueError(f'line {number}: unknown {name}')
        return state
