.PHONY: update-deps
update-deps:
	pip install --upgrade pip-tools pip setuptools
	# pip-compile --upgrade --build-isolation --generate-hashes --output-file server/requirements/main.hashed.txt server/requirements/main.in
	# pip-compile --upgrade --build-isolation --generate-hashes --output-file server/requirements/dev.hashed.txt server/requirements/dev.in
	pip-compile --upgrade --build-isolation --allow-unsafe --output-file server/requirements/main.txt server/requirements/main.in
	pip-compile --upgrade --build-isolation --allow-unsafe --output-file server/requirements/dev.txt server/requirements/dev.in

.PHONY: init
init:
	pip install --editable "./client[dev]"
	pip install --editable ./server
	pip install --upgrade -r server/requirements/main.txt -r server/requirements/dev.txt
	rm -rf ./server/.tox
	rm -rf ./client/.tox
	pip install --upgrade pre-commit tox
	pre-commit install

.PHONY: update
update: update-deps init

.PHONY: run
run:
	cd server && tox run -e=run
