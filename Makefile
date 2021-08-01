.PHONY: clean install help test lint isort run dependencies docs wheel upload
.DEFAULT_GOAL := help

help: ## Displays this help message.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


dependencies:requirements.txt
	@echo "Installing dependencies..."
	@pip install -r requirements.txt 1>/dev/null

clean: ## Remove unwanted stuff such as __pycache__, etc...
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

test: ## Runs the testsuite
	tox

run: ## Runs the development server with the development config
	flaskbb run --debugger --reload

frontend: ## Runs the webpack server which watches for changes in flaskbb/themes/aurora
	cd flaskbb/themes/aurora && npm run watch

devconfig:dependencies ## Generates a development config
	flaskbb makeconfig -d

install:dependencies ## Installs the dependencies and FlaskBB
	@[ -f ./flaskbb.cfg ] || (echo "flaskbb.cfg not found. You can generate a configuration file with 'flaskbb makeconfig'."; exit 1)
	flaskbb --config ./flaskbb.cfg install

docs: ## Builds the Sphinx docs
	$(MAKE) -C docs html

lint: ## Checks the source for style errors
	@type flake8 >/dev/null 2>&1 || echo "Flake8 is not installed. You can install it with 'pip install flake8'."
	flake8

isort:  ## Sorts the python imports
	@type isort >/dev/null 2>&1 || echo "isort is not installed. You can install it with 'pip install isort'."
	isort --order-by-type -rc -up

dist: ## Creates distribution packages (bdist_wheel, sdist)
	python setup.py sdist bdist_wheel

upload:dist ## Uploads a new version of FlaskBB to PyPI
	twine upload --skip-existing dist/*
