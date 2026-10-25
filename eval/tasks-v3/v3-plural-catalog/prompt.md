catalog.py parses source rows; add compile_catalog(source, forms) -> dict mapping
message key to {form: decoded string}. forms is a nonempty tuple of distinct
lowercase category names including 'other'. Preserve parse_rows and CatalogError.

PC1. A nonblank/non-comment line has key[form] = JSON_STRING; keys match
[A-Za-z_][A-Za-z_0-9]* and forms match [a-z]+. Optional leading whitespace and
whitespace around '=' are allowed; comments are whole lines beginning with '#'
after indentation. JSON string escapes decode exactly once; brackets and '='
inside literals are ordinary text. Preserve original 1-based line/column spans.
PC2. Collect rows by key; require exactly the supplied forms for each key.
Unknown form raises CatalogError('unknown_form', line, form_start_column).
A repeated key/form raises CatalogError('duplicate', line, key_start_column).
Process source order: syntax, unknown form, then duplicate checks on each row;
only after all rows, check missing forms in key first-appearance order and raise
CatalogError('missing_form', first_line, first_key_column). Empty source gives {}.
PC3. Invalid grammar or non-string/invalid JSON literal raises CatalogError with
code 'syntax' at that line's first non-whitespace column. Do not renumber after
blank/comment lines. Compilation must validate rows in source order, so a prior
unknown form beats a later syntax error. Add a regression test detecting an
incomplete plural key accepted without its required 'other' form.

PC4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
