PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
TEST_PATH ?=

.PHONY: skeleton test validate-schemas

# Recreate empty role-owned directories without adding implementation files.
skeleton:
	mkdir -p controller/backends controller/case_library/seed controller/prompts \
		verifier plugin/hooks plugin/skills/harness plugin/templates \
		eval/tasks eval/runner eval/baselines eval/configs eval/reports \
		docs/decisions docs/weekly docs/slides schemas/examples state \
		tests/lead tests/plugin tests/controller tests/verifier tests/eval

test:
	$(PYTHON) -m pytest $(TEST_PATH)

validate-schemas:
	$(PYTHON) docs/validate_schemas.py
