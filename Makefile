.PHONY: install run eval test docker-build docker-run

export PYTHONPATH := src

install:
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -r requirements.txt

run:
	.venv/bin/uvicorn policysight.api.main:app --reload --app-dir src --port $${POLICYSIGHT_PORT:-8000}

eval:
	.venv/bin/python -m policysight.eval.run_eval

test:
	.venv/bin/pytest -q

docker-build:
	docker build -t policysight:local .

docker-run:
	docker run --rm -p 8000:8000 policysight:local
