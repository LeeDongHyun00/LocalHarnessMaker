Extend lockfile.py with verify_offline(lock_bytes, archives) and
refresh_offline(requirements, candidates, archives, allow_prerelease=False).
archives maps exact URL strings to archive bytes. Preserve all resolver choices.

LK4. verify_offline must parse and validate the lock's exact canonical byte
representation and shape before inspecting archives. Reject noncanonical bytes,
extra/missing keys, invalid package ordering, malformed versions/sources/hashes
as ValueError('lock'). Then, in lock order, require the exact URL in archives
and a matching SHA256. Missing archive raises ValueError('missing:'+name);
wrong hash raises ValueError('digest:'+name). Return package names in lock order
on success, including [] for an empty lock. No network or disk fallback.
LK5. refresh_offline resolves by the existing version/prerelease/source/tie
policies, verifies those exact selected archives, then returns the same lock
bytes as resolve. Do not pick a lower-priority cached alternative when the
selected URL is absent or corrupt. Do not mutate arguments. Keep prior APIs,
add tests and run the same command.
