#!/usr/bin/env python3
"""Check project-pool preparation, references and checksums without running apps."""

import argparse
from collections import Counter
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "experiments" / "project-pool-v1"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    catalog = load(POOL / "catalog.json")
    provenance = load(POOL / "provenance.json")
    schema = load(POOL / "authoring" / "project-cards.schema.json")
    Draft202012Validator.check_schema(schema)
    card_validator = Draft202012Validator(schema["$defs"]["card"])
    errors = []
    total_requirements = 0
    total_scenarios = 0
    cells = Counter()
    ids = set()
    modes = Counter()

    def require(condition, message):
        if not condition:
            errors.append(message)

    require(len(catalog["projects"]) == 12, "expected 12 projects")
    require(catalog["target_project_count"] == 12, "unexpected target count")
    require(catalog["design_labels_are_not_empirical_results"], "design labels must not claim empirical validation")
    require(not provenance["training_eligible"], "unexecuted pool is not training eligible")
    success_by_domain = {
        run["domain"]: run for run in provenance["generation_attempts"]
        if run.get("exit_code") == 0 and run.get("output_generated")
    }

    for entry in catalog["projects"]:
        project_id = entry["project_id"]
        require(project_id not in ids, f"{project_id}: duplicate project")
        ids.add(project_id)
        cells[(entry["domain"], entry["work_type"])] += 1
        modes[entry["technology_design_mode"]] += 1
        source = ROOT / entry["source_path"]
        card = load(source)
        require(card["project_id"] == project_id, f"{project_id}: mismatched source id")
        require(card["domain"] == entry["domain"], f"{project_id}: mismatched source domain")
        require(digest(source) == entry["source_sha256"], f"{project_id}: changed source checksum")
        require(entry["input_status"] in ("existing_pilot_prepared", "teacher_card_reviewed"), f"{project_id}: incomplete input")
        total_requirements += len(card["requirements"])
        total_scenarios += sum(len(r["acceptance"]) for r in card["requirements"])

        if entry["source_kind"] == "existing_pilot_reference":
            require(entry["work_type"] == "new_build", f"{project_id}: reused pilot must remain new-build case")
            for profile in ("underspecified", "clear"):
                require(bool((ROOT / entry["request_refs"][profile]["path"]).read_text().strip()), f"{project_id}: missing request reference")
            continue

        for error in card_validator.iter_errors(card):
            errors.append(f"{project_id} {list(error.path)}: {error.message}")
        require(card["work_type"] == entry["work_type"], f"{project_id}: mismatched task type")
        require(card["technology_policy"]["mode"] == entry["technology_design_mode"], f"{project_id}: mismatched technology design condition")
        require(entry["domain"] in success_by_domain, f"{project_id}: missing actual teacher call")
        if entry["domain"] in success_by_domain:
            run = success_by_domain[entry["domain"]]
            require(run["model_requested"] == "gpt-6.1-sol", f"{project_id}: wrong teacher model request")
            require(digest(ROOT / run["output_source"]) == run["output_sha256"], f"{project_id}: changed teacher source")

        required_ids = [r["id"] for r in card["requirements"]]
        require(required_ids == [f"R{i}" for i in range(1, 7)], f"{project_id}: requirement ids must be R1-R6")
        require(2 <= sum(r["critical"] for r in card["requirements"]) <= 3, f"{project_id}: expected 2-3 critical requirements")
        decision_ids = [d["id"] for d in card["user_decisions"]]
        require(len(decision_ids) == len(set(decision_ids)), f"{project_id}: duplicate decision ids")
        for decision in card["user_decisions"]:
            require(set(decision["requirement_ids"]) <= set(required_ids), f"{project_id}: unknown decision requirement")
        for requirement in card["requirements"]:
            for scenario in requirement["acceptance"]:
                require(all(scenario[k].strip() for k in ("given", "when", "then")), f"{project_id}: empty acceptance field")
                require("(Then)" not in scenario["when"], f"{project_id}: expectation mixed into when")

        scopes = {r["requirement_scope"] for r in card["requirements"]}
        if entry["work_type"] == "new_build":
            require(scopes == {"deliver_new"}, f"{project_id}: new build has wrong requirement scope")
            require(card["starting_state"]["status"] == "new_workspace", f"{project_id}: unexpected start status")
        else:
            require(scopes == {"change", "preserve"}, f"{project_id}: existing task needs change and nonregression requirements")
            require(card["starting_state"]["status"] == "baseline_not_materialized", f"{project_id}: existing baseline was not built")
        if entry["work_type"] == "bug_fix":
            require(bool(card["starting_state"]["known_defects"]), f"{project_id}: missing defect blueprint")

        clear = card["initial_requests"]["clear"]
        unclear = card["initial_requests"]["underspecified"]
        require(clear["expected_question_action"] == "pass_or_enrich", f"{project_id}: clear profile must test unnecessary questions")
        require(set(clear["requirement_ids"]) == set(required_ids), f"{project_id}: incomplete clear profile declaration")
        require(not clear["omitted_decision_ids"], f"{project_id}: clear profile omits decisions")
        require(unclear["expected_question_action"] == "clarify", f"{project_id}: unclear profile must test useful questions")
        require(len(set(unclear["omitted_decision_ids"])) >= 2, f"{project_id}: unclear profile needs two missing decisions")
        require(set(unclear["omitted_decision_ids"]) <= set(decision_ids), f"{project_id}: unknown omitted decision")
        require(set(unclear["requirement_ids"]) <= set(required_ids), f"{project_id}: unknown unclear requirement")
        project = source.parent
        for profile in ("underspecified", "clear"):
            expected = card["initial_requests"][profile]["text"].strip()
            require((project / f"request-{profile}.md").read_text().strip() == expected, f"{project_id}: changed profile text")

    for domain in catalog["domains"]:
        for work_type in catalog["work_types"]:
            require(cells[(domain, work_type)] == 1, f"{domain}/{work_type}: missing or duplicate matrix cell")
    require(len(cells) == 12, "unexpected domain/task combination")
    require(modes == Counter({"candidate": 4, "maintain_existing": 4, "withhold": 4}), "unexpected technology-condition balance")

    if errors:
        for error in errors:
            print("ERROR: " + error, file=sys.stderr)
        return 1
    print(f"PASS: 12 projects, 4 domains x 3 task types, {total_requirements} requirements, {total_scenarios} acceptance scenarios")
    print("PASS: 24 clarity profiles; technology design conditions = 4 candidate / 4 maintain / 4 withhold")
    print("Preparation checks do not validate working baselines, question-policy labels or performance.")
    return 0


def inventory():
    paths = {
        p for p in POOL.rglob("*")
        if p.is_file() and p.suffix in (".md", ".json") and p.name != "hashes.json"
    }
    catalog = load(POOL / "catalog.json")
    for entry in catalog["projects"]:
        if entry["source_kind"] == "existing_pilot_reference":
            paths.add(ROOT / entry["source_path"])
            for profile in entry["request_refs"].values():
                paths.add(ROOT / profile["path"])
    paths.add(ROOT / "scripts" / "validate_project_pool.py")
    paths.add(ROOT / "requirements-preparation.txt")
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-hashes", action="store_true")
    parser.add_argument("--check-hashes", action="store_true")
    args = parser.parse_args()
    try:
        status = validate()
        if status:
            return status
        files = inventory()
        path = POOL / "hashes.json"
        if args.check_hashes:
            if load(path)["files"] != files:
                print("ERROR: checksum inventory differs", file=sys.stderr)
                return 1
            print(f"PASS: {len(files)} SHA-256 entries")
        if args.write_hashes:
            path.write_text(json.dumps({"status": "draft_inventory_not_protocol_freeze", "algorithm": "sha256", "files": files}, ensure_ascii=False, indent=2) + "\n")
            print(f"Wrote {len(files)} SHA-256 entries")
        return 0
    except (OSError, KeyError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
