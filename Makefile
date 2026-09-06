PYTHON ?= .venv/bin/python
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= $(PYTHON) -m ruff
MYPY ?= $(PYTHON) -m mypy
export PYTHONPATH := backend

.PHONY: venv install format lint typecheck test test-scientific test-integration verify-fea generate-dataset verify-reproducibility audit coverage train-surrogate run-phase2 audit-phase2 serve-api audit-phase3 audit-phase5 frontend-install frontend-dev frontend-build frontend-test frontend-e2e

venv:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

install: venv

format:
	$(RUFF) format backend tests scripts
	$(RUFF) check --fix backend tests scripts

lint:
	$(RUFF) check backend tests scripts

typecheck:
	$(MYPY) backend/app

test:
	$(PYTEST) tests/unit

test-scientific:
	$(PYTEST) tests/scientific

test-integration:
	$(PYTEST) tests/integration

coverage:
	$(PYTEST) --cov=app --cov-report=term-missing tests

verify-fea:
	$(PYTHON) scripts/verify_fea.py

generate-dataset:
	$(PYTHON) scripts/generate_dataset.py --config configs/scientific.yaml

verify-reproducibility:
	$(PYTHON) scripts/verify_reproducibility.py --config configs/scientific.yaml

audit:
	$(PYTHON) scripts/audit_dataset.py --config configs/scientific.yaml

train-surrogate:
	$(PYTHON) scripts/train_surrogate.py --phase1-config configs/scientific.yaml --phase2-config configs/phase2.yaml

run-phase2:
	$(PYTHON) scripts/run_phase2.py --phase1-config configs/scientific.yaml --phase2-config configs/phase2.yaml

audit-phase2:
	$(PYTHON) scripts/audit_phase2.py

serve-api:
	$(PYTHON) -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

audit-phase3:
	$(PYTHON) scripts/audit_phase3.py

audit-phase5:
	$(PYTHON) scripts/audit_phase5.py

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm run lint && npm run typecheck && npm test

frontend-e2e:
	cd frontend && npm run e2e
