"""Select baseline C using public metadata only; never fill human guidance."""

import json
from pathlib import Path
import random
from typing import Any

FROZEN_DIGEST = "b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f"


def select(tasks: Path, seed: int = 0) -> list[dict[str, Any]]:
    """Shuffle sorted metadata strata and greedily take five unused families each."""
    rows = [json.loads(p.read_text()) for p in sorted(tasks.glob("*/meta.json"))]
    rows = [r for r in rows if not r["two_session"]]
    rng = random.Random(seed)
    used: set[str] = set()
    selected = []
    for kind in sorted({r["type"] for r in rows}):
        candidates = sorted((r for r in rows if r["type"] == kind), key=lambda r: r["id"])
        rng.shuffle(candidates)
        count = 0
        for row in candidates:
            # Legacy metadata lacks family; its public ID supplies the family.
            family = row.get("family", row["id"].removeprefix("bug-"))
            if family not in used:
                selected.append({"task_id": row["id"], "family": family, "type": kind})
                used.add(family)
                count += 1
                if count == 5:
                    break
        if count != 5:
            raise ValueError("Insufficient unused families in stratum")
    return sorted(selected, key=lambda r: r["task_id"])


def main() -> None:
    """Create reviewable skeletons, refusing to overwrite existing human work."""
    root = Path(__file__).resolve().parents[2]
    rows = select(root / "eval/tasks")
    baseline = root / "eval/baselines"
    manifest = {"seed": 0, "frozen_task_set_sha256": FROZEN_DIGEST,
                "procedure": "Read only sorted public */meta.json; exclude two_session. Iterate type strings lexicographically. Use one Python random.Random(0), shuffle ID-sorted candidates per type, greedily select first five whose family has not appeared in any stratum. Legacy bug-chunk-tail lacks family: use chunk-tail from its ID. Sort selected IDs lexicographically. No run evidence is read.",
                "tasks": rows}
    (baseline / "c-subset.json").write_text(json.dumps(manifest, indent=2) + "\n")
    template = (baseline / "template.md").read_text()
    for row in rows:
        task = row["task_id"]
        with (baseline / "c" / f"{task}.md").open("x") as stream:
            stream.write(f"Task ID: {task}\nPublic prompt: eval/tasks/{task}/prompt.md\n\n" + template)
    config = json.loads((root / "eval/configs/full-a.yaml").read_text())
    config.update(name="full-c", tasks=[r["task_id"] for r in rows], static_template_dir="eval/baselines/c", task_population=config["tasks"])
    config["task_timeout_seconds"] = {t: config["task_timeout_seconds"][t] for t in config["tasks"]}
    (root / "eval/configs/full-c.yaml").write_text(json.dumps(config, indent=2) + "\n")


if __name__ == "__main__":
    main()
