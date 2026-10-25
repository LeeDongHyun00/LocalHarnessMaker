Add export_range(shifts, holidays, begin, end) to shifts.py. It returns a list of
{'start': ISO datetime, 'end': ISO datetime, 'name': string, 'priority': integer}
objects with second precision, clipped to the datetime range from begin to end using the existing boundary
convention. An empty/reversed range returns [].

SH4. Include occurrences that begin before the requested datetime range and
still overlap it, then resolve and clip using the retained compiler's policies.
The export must agree with compile_shifts on overlapping weekly/exceptional
shifts, including those across midnight and the date-range edges.
SH5. Export must preserve deterministic tie resolution, holiday precedence and
coalescing, without changing inputs. Do not restate or replace the existing
policy values. Retain all old signatures; add tests and run the same command.
