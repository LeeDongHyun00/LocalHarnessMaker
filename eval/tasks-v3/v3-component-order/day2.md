Add Graph.update(additions=(), removals=()) in components.py for batches of
edge changes. Retain the original node universe and all previous output policies.

CO4. Validate every endpoint in both iterables before making any changes;
unknown endpoints raise the established error and leave the graph unchanged.
Apply all removals, then all additions. Missing removals and duplicate additions
are harmless. A pair occurring in both ends present. Snapshot caller iterables.
CO5. After update, condensation must correctly merge and split components,
preserve representatives for unchanged memberships and obey the existing
ordering/tie policies, including newly released ready components. Repeated
updates and returned-result mutation must not leak state. Full recomputation is
allowed; no performance claim beyond the original chain requirement. Add tests
and run the same command.
