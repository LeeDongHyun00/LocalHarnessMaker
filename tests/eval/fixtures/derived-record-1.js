const original = load("original_sources");
const records = [...original.matchAll(/^FILE ([^\n]+) SHA256 ([a-f0-9]{64})\n([\s\S]*?)(?=^FILE |\s*$)/gm)];
const protectedNames = new Set(["README.md", "verify.py", "test_public.py", "project/compat.py"]);
const hashes = Object.fromEntries(records.filter(r => protectedNames.has(r[1])).map(r => [r[1], r[2]]));
store("protected_hashes",hashes);
const checks = await Promise.allSettled([
  tools.exec_command({cmd:"python verify.py","max_output_tokens":6000}),
  tools.exec_command({cmd:"python - <<'PY'\nimport hashlib\nimport inspect\nfrom pathlib import Path\nfrom project import engine, policy, render, render_many, run, run_many, validation\nexpected = "+JSON.stringify(hashes)+"\nassert len(expected) == 4\nfor name, digest in expected.items():\n    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name\nprint('Protected files: all 4 unchanged byte for byte')\nfor api in (run, render, run_many, render_many, engine.compute, validation.validate, policy.normalize):\n    signature = inspect.signature(api)\n    assert len(signature.parameters) == 1\n    assert all(p.annotation is not inspect.Parameter.empty for p in signature.parameters.values())\n    assert signature.return_annotation is not inspect.Signature.empty\n    print(f'{api.__module__}.{api.__name__}{signature}')\nPY","max_output_tokens":3000})
]);
for(let i=0;i<checks.length;i++) text({index:i,...checks[i]});
store("verification_run",checks[0]);
