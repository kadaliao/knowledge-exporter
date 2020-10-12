clean:
	rm -rf build
	rm -rf dist
	rm -rf knowledge_exporter.egg-info

build:
	python setup.py sdist
	python setup.py bdist_wheel

deploy:
	twine upload dist/*
