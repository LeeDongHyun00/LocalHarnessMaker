Convert emitter.render(node) from recursive traversal to an explicit event stack. Preserve serialized output bytes for every valid input. There is no HTML parser or DOM dependency.
HE1. A node is either a str text node or a tuple (tag, attributes, children). tag is a valid nonempty HTML name. attributes is an ordered list of (name, string_value) pairs; duplicate names are retained. children is a list of valid nodes. Emit <tag>, then children in order, then </tag>, including empty elements; do not special-case void elements. Emit each attribute as one space, its name, =, and a double-quoted escaped value in supplied order.
HE2. Escape &, < and > in text; escape those plus double quote as &quot; and apostrophe as &#x27; in attributes. Text quotes stay literal. No whitespace, newline or normalization is added. Return a str and preserve Unicode code points.
HE3. Use an explicit event stack, with no recursive application traversal and no changes to the process recursion limit. Support depth 2400 and siblings around nested nodes. Never mutate nodes, attribute lists or child lists; input objects may be shared between parents.
HE4. Keep render(node: str | tuple) -> str callable with the same signature; repeated calls and a standalone empty text node produce deterministic independent results. Add regression tests for byte equality and deep nesting.

Use Python 3.11+ and the standard library. Add regression tests as needed.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
