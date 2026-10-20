.PHONY: install run debug clean lint lint-strict

MAP ?= /sgoinfre/radakrou/fly-in/maps/easy/01_linear_path.txt
PYTHON = .venv/bin/python3

install:
	test -d .venv || python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) main.py $(MAP)

debug:
	$(PYTHON) -m pdb main.py $(MAP)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache

lint:
	@fail=0; \
	$(PYTHON) -m flake8 . || fail=1; \
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs || fail=1; \
	exit $$fail

lint-strict:
	@fail=0; \
	$(PYTHON) -m flake8 . || fail=1; \
	$(PYTHON) -m mypy . --strict || fail=1; \
	exit $$fail
