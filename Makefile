.PHONY: clean install help test lint run dependencies docs

help:
	@echo "  clean      remove unwanted stuff"
	@echo "  install    install dependencies and flaskbb"
	@echo "  devconfig  generates a development config"
	@echo "  test       run the testsuite"
	@echo "  lint       check the source for style errors"
	@echo "  run        run the development server with the development config"
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
	py.test

run:
	flaskbb run --debugger --reload

devconfig:dependencies
	flaskbb makeconfig -d

install:dependencies
	@[ -f ./flaskbb.cfg ] || (echo "flaskbb.cfg not found. You can generate a configuration file with 'flaskbb makeconfig'."; exit 1)
	flaskbb --config ./flaskbb.cfg install

docs:
	$(MAKE) -C docs html

lint:check
	flake8

check:
	@type flake8 >/dev/null 2>&1 || echo "Flake8 is not installed. You can install it with 'pip install flake8'."
