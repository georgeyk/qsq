.PHONY: clean-pyc

default: test

clean-pyc:
	@find . -iname '*.py[co]' -delete
	@find . -iname '__pycache__' -delete
	@find . -iname '.coverage' -delete
	@rm -rf htmlcov/

clean-dist:
	@rm -rf dist/
	@rm -rf build/
	@rm -rf *.egg-info

clean-tox:
	@rm -rf .tox/

clean: clean-pyc clean-dist clean-tox

test:
	py.test -vv tests

test-cov:
	py.test -vv --cov=qsq tests

cov:
	coverage report -m

cov-report:
	py.test -vv --cov=qsq --cov-report=html tests

tox:
	tox -r

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel

release: dist
	git tag `python setup.py -q version`
	git push origin `python setup.py -q version`
	twine upload dist/*

changelog-preview:
	@echo "\nmaster ("$$(date '+%Y-%m-%d')")"
	@echo "-------------------\n"
	@git log $$(python setup.py -q version)...master --oneline --reverse