const original = load("original_sources");
const headers = [...original.matchAll(/^FILE (\S+) SHA256 [a-f0-9]{64}\n/gm)];
const sources = {};
for (let i=0; i<headers.length; i++) {
  const header = headers[i];
  sources[header[1]] = original.slice(header.index+header[0].length, i+1<headers.length?headers[i+1].index:original.length).slice(0,-1);
}
text(await tools.exec_command({
  cmd:"python - <<'PY'\nimport ast\nimport difflib\nimport json\nfrom pathlib import Path\noriginal = json.loads("+JSON.stringify(JSON.stringify(sources))+")\nfor name, before in original.items():\n    path = Path(name)\n    assert path.is_file(), f'Missing original file: {name}'\n    after = path.read_text()\n    if name.endswith('.py'):\n        old_functions = {node.name: node for node in ast.parse(before).body if isinstance(node, ast.FunctionDef)}\n        new_functions = {node.name: node for node in ast.parse(after).body if isinstance(node, ast.FunctionDef)}\n        for function, old in old_functions.items():\n            new = new_functions[function]\n            assert ast.dump(old.args) == ast.dump(new.args), (name, function)\n            assert ast.dump(old.returns) == ast.dump(new.returns), (name, function)\n    if before != after:\n        print(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=name + ' (original)', tofile=name)), end='')\nprint('All original files and function signatures retained.')\nreport = json.loads(Path('verification.json').read_text())\nassert report == {'command': ['python', 'verify.py'], 'passed_tests': 20, 'failed_tests': 0}, report\nprint('Generated verification.json:', json.dumps(report, sort_keys=True))\nPY",
  max_output_tokens:5000
}));
