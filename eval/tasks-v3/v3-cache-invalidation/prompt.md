Complete tagcache.py's tagged cache and maintenance.py CLI. APIs: Cache(capacity),
put(namespace,key,value,tags), get(namespace,key)->(found,value),
invalidate(namespace,tags)->list[str], clear(namespace)->list[str], stats(namespace),
snapshot(), Cache.restore(snapshot). Names/keys/tags are strings, values JSON.
No concurrency or TTL is required.

CI1. Capacity is per namespace, nonnegative; negative raises ValueError('capacity'). put replaces a key's value AND tags, marks it most recently used, and copies caller data. get marks hits most recent and returns a detached value; missing returns (False,None), distinct from a stored None. On capacity overflow evict the least recently used entry in that namespace only. Capacity zero immediately evicts every put.
CI2. invalidate removes the union of entries bearing any requested tag in the specified namespace; duplicate/unknown tags are harmless. Return unique removed keys sorted by Python string order. Replacement and eviction must remove obsolete tag memberships. clear removes every key only in its namespace and returns sorted keys. Empty invalidation does nothing.
CI3. stats returns exactly hits, misses, evictions, invalidations, entries as integers. Only get changes hit/miss counts; capacity evictions increment evictions; explicit invalidate/clear increment invalidations by distinct removed entries. Replacement is neither. Unknown namespace stats are all zero and read-only; return detached counters.
CI4. snapshot returns {'capacity':N,'entries':[[namespace,key,value,sorted_tags],...], 'counters':{namespace:{hits,misses,evictions,invalidations}}}. Entries are namespace-sorted, then least-to-most-recent within each; include counters for all namespaces touched by put/get/invalidate/clear, even empty ones. restore accepts valid snapshots and preserves LRU order, tags, values and counters. Neither direction shares mutable structures.
CI5. `python maintenance.py STATE stats NAMESPACE`, `... invalidate NAMESPACE [TAG...]`, `... clear NAMESPACE` load a valid snapshot JSON file. stats emits {'stats':...} without rewriting bytes. Mutations atomically replace STATE with the new snapshot and emit {'removed':sorted_keys,'stats':...}. stdout is one sort_keys=True JSON line, exit 0, empty stderr. Missing/unreadable file, invalid JSON, negative capacity, missing required snapshot keys or invalid command arguments: exit 2, empty stdout, stderr exactly 'cache maintenance failed' plus newline. Preserve original bytes and remove temporary siblings on failure. Add CACHE.md naming all three commands and explaining per-namespace LRU, overlapping-tag union and counters.

Use Python 3.11+ and only the standard library. Preserve the stated APIs.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
