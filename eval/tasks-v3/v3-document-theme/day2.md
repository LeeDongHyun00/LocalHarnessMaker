Extend theme.py with render_print(tree, rules). Rules may now additionally carry
a print dict of property overrides; nodes may carry a print dict as well.

DT4. Compute a print tree with the established cascade, inheritance and reset
rules. At each specificity, apply each rule's style then its print entries;
apply node style then node print last. Inheritance uses the parent's computed
PRINT style. Print must not alter a later ordinary resolve result.
DT5. Return {'nodes': flat_preorder_rows, 'resources': resource_mapping}. Each row
has exactly id, text (HTML escaped including quotes), style and resource. Omit
nodes whose computed display is 'none' AND their entire subtree from nodes,
but retain their resources in the mapping. Resource identity/order must agree
with the preceding session's policy. Keep prior APIs and signatures; add tests
and run the same command.
