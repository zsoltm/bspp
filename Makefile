format:
	black bspp tests

lint:
	black --check bspp tests
	pylint --rcfile .pylint bspp/*.py
	mypy bspp/*.py

release: lint test
	flit publish

test:
	python -m unittest -v tests
