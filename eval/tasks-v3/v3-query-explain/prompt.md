Complete query.py's AST parser, safe filter pushdown, explain output and legacy
adapter. APIs: parse(source)->dict, plan(ast)->dict, execute(documents,query)->dict,
search(documents,request)->list, QueryError(position). Documents have unique id,
text and optional string-valued filter fields; do not mutate inputs.

QE1. Grammar: identifiers [A-Za-z_][A-Za-z0-9_]*, words or field=value atoms, parentheses, uppercase AND/OR. Whitespace is optional between punctuation; AND binds tighter than OR; both associate left. Operators cannot be words or filter values. AST word has type='word',value,span; filter has type='filter',field,value,span; binary has type='and'/'or',left,right,span. span is [start,end] in 0-based characters, end exclusive; parentheses expand their inner root's span. No other AST fields.
QE2. Reject empty/whitespace-only input at position 0. Reject illegal characters at their position before parsing. For grammar errors use the next unexpected token's start or len(source) at EOF. QueryError.position is that integer, str(error) is 'query at N'. Never accept trailing operands/tokens.
QE3. plan returns exactly filters (list of {'field','value'}) and residual (AST or None). Recursively split only AND nodes reachable from the root through AND nodes, collecting filter leaves left-to-right, preserving duplicates. Never push a filter from inside OR. Remove pushed leaves; collapse one-sided ANDs; remaining binary nodes retain original spans. Explain must be detached from its input AST.
QE4. A word matches a casefolded whitespace-delimited text token; filters compare exact field values, absent fields do not match. AND/OR have Boolean meaning. execute uses its own explain plan and returns {'ids':[matching ids in input order], 'explain':plan}; semantics must equal the unoptimized AST. Filter-only residual None matches all remaining documents.
QE5. search supports a query string and legacy {'term':query_string,'filters':mapping}. Legacy filters are extra AND constraints sorted by field name, with the term parenthesized to preserve OR semantics; legacy terms are nonempty and values/keys are grammar identifiers. Return ids only. Include QUERY.md with grammar precedence, explanation of why OR filters cannot be pushed, and a fenced json legacy example with at least two filters that search accepts.

Use Python 3.11+ and only the standard library. Preserve the stated APIs.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
