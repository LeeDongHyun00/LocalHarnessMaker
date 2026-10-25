import json
from pathlib import Path
import subprocess
from collections.abc import Callable
from typing import Any

def build(root: str | Path, output_dir: str | Path, launcher: Callable[...,Any] = subprocess.run) -> list[Any]:
    root = Path(root).resolve()
    jobs = json.loads((root/'manifest.json').read_text())['jobs']
    names = set()
    results = []
    for job in jobs:
        name,source = job['name'],job['source']
        if name in names: raise ValueError('duplicate: ' + name)
        names.add(name)
        path = (root/source).resolve()
        if not path.is_relative_to(root): raise ValueError('outside: ' + source)
        if not path.is_file(): raise FileNotFoundError(source)
        argv = ['builder','--input',str(path),'--output',str(Path(output_dir)/(name+'.o'))]
        results.append(launcher(argv,shell=False,check=True))
    return results
