Implement the package lock resolver in lockfile.py using Python 3.11+ and the
standard library. resolve(requirements, candidates, allow_prerelease=False)
returns lock bytes. requirements maps package name to a minimum stable version
'X.Y.Z'. Each candidate has exactly name, version, source, url, sha256. Sources
are workspace, mirror or registry; hashes are lowercase 64-character SHA256.
Candidates/requirements are valid and candidates with a given name/version/source/
URL have identical hashes. Dependencies are already expanded in requirements.

LK1. Choose independently per package among versions with a numeric (X,Y,Z)
base >= its minimum. Stable versions outrank ALL prereleases. If no suitable
stable exists, prereleases are eligible only when allow_prerelease=True.
Versions are either X.Y.Z or X.Y.Z-label.N, with lowercase alphabetic label
and nonnegative numeric N. Within stables use greatest numeric tuple; within
prereleases use greatest (X,Y,Z,label,N), with lexical label and numeric N.
Unsatisfied packages raise ValueError('unresolved:'+name), choosing the first
name in sorted requirement order when several fail. No network/ambient files.
LK2. After choosing a version, choose its source by workspace before mirror
before registry, then lexicographically smallest URL. Input order and duplicate
candidates must not change resolution. Never mutate caller data.
LK3. Lock bytes are UTF-8 JSON {'packages': [selected_candidate,...]} with rows
sorted by name, sorted object keys, compact separators, ensure_ascii=True and
exactly one final LF. Retain all five candidate fields; do not add a clock or
filesystem path. Empty requirements yields an empty packages list. Keep the
function signature, add regression tests and run
python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
