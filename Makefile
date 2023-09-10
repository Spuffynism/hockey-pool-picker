bootstrap:
	pip3 install -r requirements.txt

run:
	python3 main.py

lint:
	black . && ruff check --fix .

crawl:
	python3 source/capfriendly.py
	python3 source/hockey_reference.py
