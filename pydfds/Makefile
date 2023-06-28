build:
	rm -rf dist/
	python -m build
	twine check dist/*

publish-test:
	twine upload -r testpypi dist/*

publish:
	twine upload -r pypi dist/*