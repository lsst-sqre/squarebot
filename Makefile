.PHONY: install
install:
	pip install -e ".[dev]"

.PHONY: test
test:
	pytest

.PHONY: dev
dev:
	adev runserver --app-factory create_app sqrbot/app.py

.PHONY: image
image:
	python setup.py sdist
	docker build --build-arg VERSION=`sqrbot --version` -t lsstsqre/sqrbot-jr:build .

.PHONY: travis-docker-deploy
travis-docker-deploy:
	./bin/travis-docker-deploy.sh lsstsqre/sqrbot-jr build

.PHONY: version
version:
	sqrbot --version
