format:
	black bspp

lint:
	black --check bspp
	pylint --rcfile .pylint bspp/*.py

release: lint test
	flit publish
