Add diff_config(before, after, secret_fields) and export_diff with the same
arguments to inspection.py. Retain the original inspector's policies.

SR4. Diff compares raw scalar leaves by path, including type (bool differs from
integer). Return only added/removed/changed paths, in the established order.
Each row has exactly path, before, after, before_present, after_present, secret.
Missing sides use None and a false presence flag. If either side of a changed
path is secret, mask BOTH present sides using the established mask; secret=true.
Still report changed secret values even when their redacted views match. A
container-to-scalar replacement produces removed child paths plus its new leaf.
SR5. export_diff returns canonical JSON of the diff rows, using the existing
serialization choices. No raw secret may leak through changed or nested values,
including after a type replacement; secrecy follows the respective tree's
ancestry. Empty containers still have no leaves. Accept generator secret names
for both sides and do not modify the inputs. Add tests and run the same command.
