.PHONY: clean install help test lint isort run dependencies docs wheel upload dev-plugins
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
	uv run pytest

run: ## Runs the development server with the development config
	WERKZEUG_DEBUG_PIN=off uv run flaskbb run --debugger --reload --debug

frontend: ## Runs the webpack server which watches for changes in flaskbb/themes/aurora
	cd flaskbb/themes/aurora && npm run watch

frontend-dark: ## Runs the webpack server which watches for changes in flaskbb/themes/aurora
	cd flaskbb/themes/aurora && npm run watch

dev-plugins: ## Install the plugins as editable
	uv pip install -e ../flaskbb-plugin-portal -e ../flaskbb-plugin-conversations

devconfig:dependencies ## Generates a development config
	uv run flaskbb makeconfig -d

install:dependencies ## Installs the dependencies and FlaskBB
	uv run flaskbb install

upload: ## Uploads to PyPI
	twine upload dist/{*.tar.gz,*.whl} --skip-existing

docs: ## Builds the Sphinx docs
	uv run sphinx-build -b html docs docs/_build/html

format: ## Sorts the imports and reformats the code
	# sort imports / remove unused
	uv run ruff check --fix --select I
	uv run ruff check --fix
	# reformat
	uv run ruff format
