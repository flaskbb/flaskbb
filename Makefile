.PHONY: clean install help test lint isort run dependencies docs wheel upload

help:
	@echo "  clean      remove unwanted stuff"
	@echo "  install    install dependencies and flaskbb"
	@echo "  devconfig  generates a development config"
	@echo "  test       run the testsuite"
	@echo "  lint       check the source for style errors"
	@echo "  isort      sort the python imports"
	@echo "  run        run the development server with the development config"
	@echo "  dist       creates distribution packages (bdist_wheel, sdist)"
	@echo "  upload     uploads a new version of FlaskBB to PyPI"
	@echo "  docs       build the documentation"

dependencies:requirements.txt
	@echo "Installing dependencies..."
	@pip install -r requirements.txt 1>/dev/null

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

test:
	tox

run:
	flaskbb run --debugger --reload

devconfig:dependencies
	flaskbb makeconfig -d

install:dependencies
	@[ -f ./flaskbb.cfg ] || (echo "flaskbb.cfg not found. You can generate a configuration file with 'flaskbb makeconfig'."; exit 1)
	flaskbb --config ./flaskbb.cfg install

docs:
	$(MAKE) -C docs html

lint:check-flake8
	flake8

check-flake8:
	@type flake8 >/dev/null 2>&1 || echo "Flake8 is not installed. You can install it with 'pip install flake8'."

isort:check-isort
	isort --order-by-type -rc -up

check-isort:
	@type isort >/dev/null 2>&1 || echo "isort is not installed. You can install it with 'pip install isort'."

dist:
	python setup.py sdist bdist_wheel

upload:dist
	twine upload --skip-existing dist/*
