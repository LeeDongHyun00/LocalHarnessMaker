Build the shift recurrence compiler in shifts.py. Shift is a frozen dataclass
(name: str, weekday: int, start: int, end: int, priority: int=0). weekday follows
Monday=0. Minute offsets are in [0,1440); end <= start denotes an overnight shift
ending on the following day, including a full day when equal. Input values are
valid. Use naive datetime/date values, Python 3.11+ and the standard library.

SH1. compile_shifts(shifts, holidays, first, stop) produces sorted tuples
(start_datetime, end_datetime, name, priority) for occurrences whose start DATE
is in [first,stop). holidays maps date to either None (closed) or a list of
Shift objects to use on that date regardless of their weekday. A holiday entry
completely replaces weekly recurrence, rather than adding to it. Closed days
cancel shifts starting that date only; a preceding overnight shift survives.
SH2. All time intervals are half open. Resolve overlaps by greatest priority,
then lexicographically smallest name. Split at every relevant boundary and
coalesce touching segments of the same name AND priority. Sort by start;
no output segment overlaps another. Do not clip overnight ends to stop. Return
[] for an empty/reversed date range. Do not mutate shifts or holidays.
SH3. Duplicate identical occurrences do not duplicate output. The compiler must
use dates rather than wall-clock/timezone conversions. Keep the dataclass and
function signature. Add tests as needed; run
python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
