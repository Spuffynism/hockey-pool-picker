bootstrap:
	pip3 install -r requirements.txt

run:
	python3 main.py

pick-2023:
	python3 pick_2023.py

lint:
	black . && ruff check --fix .

crawl:
	python3 source/cap_friendly.py
	python3 source/hockey_reference.py

crawl-salaries:
	python3 source/cap_friendly.py
