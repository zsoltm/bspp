format:
	black bspp tests

pylint:
	pylint --rcfile .pylint bspp/*.py

lint: pylint
	black --check bspp tests
	mypy bspp/*.py

lint_3.9:
    # pylint is currently not compatible with python 3.9: https://github.com/PyCQA/pylint/issues/3882
	black --check bspp tests
	mypy bspp/*.py

clean:
	rm -Rf dist

release: clean lint test
	flit publish

test:
	python -m unittest -v tests
