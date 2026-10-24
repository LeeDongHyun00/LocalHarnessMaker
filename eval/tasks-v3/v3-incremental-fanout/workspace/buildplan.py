from snapshots import Previous, Stamp


def plan(previous: dict[str, Previous], current: dict[str, list[str]],
         sources: dict[str, Stamp], outputs: dict[str, Stamp]) -> list[str]:
    dirty: dict[str, bool] = {}
    active: set[str] = set()
    order: list[str] = []
    def visit(name: str) -> bool:
        if name in active:
            raise ValueError('cycle:' + name)
        if name in dirty:
            return dirty[name]
        active.add(name)
        old = previous.get(name)
        changed = old is None or name not in outputs or any(dep not in old.dependencies for dep in current[name])
        for dep in current[name]:
            if dep in current:
                child_dirty = visit(dep)
                changed = changed or child_dirty
            else:
                if dep not in sources:
                    raise ValueError('missing:' + dep)
                if old is None or old.input_digests.get(dep) != sources[dep].digest:
                    changed = True
        active.remove(name)
        dirty[name] = changed
        if changed:
            order.append(name)
        return changed
    for name in sorted(current):
        visit(name)
    return order
