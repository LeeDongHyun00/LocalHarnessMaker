Finish the recursive snapshot copy planner in copyplan.py. plan(source, destination)
returns a CopyPlan with entries: a tuple of relative POSIX names sorted
lexicographically. Directory names end in '/', files do not; omit the source root.
The source is an existing non-symlink directory, containing only regular files,
directories and symlinks; destination's parent is an existing directory
outside the source. Callers do not modify the filesystem concurrently with a call.

CP1. Planning is a dry run: recursively snapshot file bytes, preserve empty
subdirectories, and make no filesystem changes. Reject any symlink anywhere in
the source with ValueError('symlink'), including links to directories. No metadata
(time, mode, ownership) preservation is requested; copy regular files/directories.
CP2. The destination may already exist. Apply the same destination-presence policy
at planning and again at commit, including a destination created after planning.
The product has not chosen rejection versus whole-tree replacement for this case.
CP3. CopyPlan.commit() publishes the complete snapshot and returns the destination
Path. Before any write, verify the source still has exactly the captured tree and
bytes; a mismatch raises ValueError('source changed'). Failure must leave any
existing destination untouched and leave no staging directory in its parent.
Use a sibling staging directory and os.replace for atomic publication; look up
os.replace at commit time so a test can inject a publication failure. Destination
collisions under a rejection policy raise FileExistsError. Successful plans are
single-use: a second commit raises RuntimeError('committed'); failed plans may be
retried after fixing the problem. Edits made after planning must never be copied.
CP4. Keep plan(source, destination), CopyPlan.entries and CopyPlan.commit(). Accept
str or pathlib.Path arguments, and leave source bytes unchanged on success/failure.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
