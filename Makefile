.PHONY: clean

help:
	    @echo "  clean      remove unwanted stuff"
	    @echo "  install    install testend"
	    @echo "  tests       run the testsuite"
	    @echo "  run        run the development server"

clean:
	    find . -name '*.pyc' -exec rm -f {} +
	    find . -name '*.pyo' -exec rm -f {} +
	    find . -name '*~' -exec rm -f {} +
	    find . -name '__pycache__' -exec rm -rf {} +

test:
	    py.test --cov=flaskbb --cov-report=term-missing tests

run:
	    python manage.py runserver

install:
	    python manage.py install
