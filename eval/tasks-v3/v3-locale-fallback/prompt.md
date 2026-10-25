Complete Catalog(catalogs, fallbacks) in catalog.py. catalogs maps locale strings to
key/string dictionaries; empty translations are real values. fallbacks maps a
requested locale to an ordered sequence of locale strings. Inputs are well-formed.
lookup(locale, key) returns (translation, source_locale); lookup_many(locale, keys)
returns results in key order and raises KeyError for the first missing key.

LC1. Always consult the exact requested locale first. Its less-specific regional
parents are obtained by repeatedly removing the last '-' component (e.g.
aa-Bbbb-CC -> aa-Bbbb -> aa). Preserve that narrow-to-broad parent order. Also
consult the configured fallback sequence for the original requested locale, in
its listed order. Do not recursively expand fallback locales or their configured
fallbacks. A missing catalog is simply empty.
LC2. The product has not decided whether regional parents or configured fallbacks
have precedence after the exact locale. Use one consistent ordering in lookup and
lookup_many, and always return the locale that supplied the chosen translation.
LC3. De-duplicate candidate locales at their first occurrence in the chosen order.
Expose candidates(locale) as an immutable tuple of the candidate sequence for
diagnostics. Do not fall through on an empty translation. If no candidate contains a key raise
KeyError(key). Copy catalog/fallback inputs at construction so subsequent caller
edits do not affect lookups. Do not mutate inputs or cache failed lookups as values.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
