Implement a document stylesheet cascade in theme.py. A node is a dict with id,
tag, optional text (default ''), optional style dict, optional resource URL, and
children (default []). IDs are unique; tags and IDs are plain nonempty strings.
Rules are a list of {'selector': tag_or_#id, 'style': dict}. Property keys are
color, font, margin, display. Values are strings except margin, an integer.
The reserved value 'reset' is allowed for every property. Inputs are valid.
Use Python 3.11+ and the standard library.

DT1. resolve(tree, rules) returns a new tree with exactly id, tag, text, style,
resource, children on every node. Defaults are color='black', font='serif',
margin=0, display='block'. Only color and font inherit computed parent values;
other properties start at defaults on each node. A reset selects the property's
DEFAULT, including for inherited properties; absence keeps the current value.
DT2. Tag rules apply before ID rules, later rules win within one specificity,
and inline style wins over rules. A rule matches only its exact tag or ID.
Never mutate the source tree or rules, and returned trees must not alias input
containers. resource is None if absent, otherwise stable_name(URL), defined as
'r-' plus the first 12 lowercase hex characters of SHA256 of the exact UTF-8 URL
plus '.bin'. Identical URLs share a name regardless of node position; do not
normalize URLs or use Python's process-randomized hash.
DT3. resources(tree) returns a dict mapping stable names to original URLs,
including all nodes in preorder (even display='none'); repeated URLs appear once.
Maintain insertion order. No file/network I/O. Export stable_name, resolve,
resources. Add regression tests as needed and run
python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
