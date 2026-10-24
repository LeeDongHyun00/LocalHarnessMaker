Repair Histogram.merge in histogram.py. These are disjoint bucket counters with
a separate overflow bin, but a merge currently counts overflow samples twice.
Keep Histogram(bounds), observe(value), merge(other), counts, overflow and total.

HG1. bounds is a strictly increasing nonempty sequence of finite numbers. Copy it
at construction; reject empty, repeated, unsorted or nonfinite bounds with
ValueError('bounds'). Bucket i includes values > the previous bound and <= bound i;
the first includes all values <= its bound. Values above the last go to overflow.
Reject NaN/infinite observations with ValueError('sample') without changing counts.
HG2. counts is a list of per-bucket counts; overflow is a separate integer; total
is the sum of all buckets and overflow. Every observation increases total by one.
HG3. merge returns a new independent Histogram with elementwise sums only when
bounds match exactly; otherwise raise ValueError('incompatible') before mutation.
Never mutate either operand, including merging an object with itself. Merge is
associative; empty histograms are identities. Changes to the returned histogram
must not alter either original or the caller's bounds list.

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
