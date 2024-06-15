build:
	rm -rf dist/
	pip-compile pyproject.toml
	python -m build
	twine check dist/*

publish-test:
	twine upload -r testpypi dist/*

publish:
	twine upload -r pypi dist/*