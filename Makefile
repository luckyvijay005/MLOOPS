.PHONY: setup sample-data download-data pipeline dashboard test docker-up docker-down clean

PYTHON ?= python

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

sample-data:
	$(PYTHON) scripts/generate_sample_data.py

download-data:
	$(PYTHON) src/ingestion/download_dataset.py

pipeline:
	$(PYTHON) scripts/run_pipeline.py

pipeline-sample:
	$(PYTHON) scripts/run_pipeline.py --dataset-path data/sample/synthetic_diabetic_data.csv

dashboard:
	$(PYTHON) scripts/run_dashboard.py

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

docker-up:
	docker compose up -d postgres

docker-down:
	docker compose down

presentation:
	$(PYTHON) scripts/generate_presentation.py

clean:
	rm -rf __pycache__ .pytest_cache
