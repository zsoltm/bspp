format:
	black bspp tests

lint:
	black --check bspp tests
	pylint --rcfile .pylint bspp/*.py
	mypy bspp/*.py

clean:
	rm -Rf dist

release: clean lint test
	flit --repository testpypi publish

test:
	python -m unittest -v tests
