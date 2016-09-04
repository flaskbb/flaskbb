.PHONY: clean install help test run dependencies docs

help:
	@echo "  clean      remove unwanted stuff"
	@echo "  install    install flaskbb and setup"
	@echo "  test       run the testsuite"
	@echo "  run        run the development server"
	@echo "  docs       build the documentation"

dependencies:requirements.txt
	pip install -r requirements.txt

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

test:
	py.test

run:
	python manage.py runserver -dr

install:dependencies
	clear
	python manage.py install

docs:
	$(MAKE) -C docs html
