bootstrap:
	pip3 install -r requirements.txt

run:
	python3 main.py

lint:
	black . && ruff check --fix .
