.PHONY: clean

help:
	    @echo "  clean       remove unwanted stuff"
	    @echo "  release     package and upload a release"
	    @echo "  develop     make a development package"
	    @echo "  sdist       package"

clean:
	    find . -name '*.pyc' -exec rm -f {} +
	    find . -name '*.pyo' -exec rm -f {} +
	    find . -name '*~' -exec rm -f {} +

release: register
	    python setup.py sdist upload

register:
	    python setup.py register

sdist:
	    python setup.py sdist

develop:
	    python setup.py develop
