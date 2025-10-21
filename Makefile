build-docs:
	cd docs && uv run quartodoc build --verbose && quarto render

preview:
	cd docs && quarto preview

test:
	pytest --cov-report=xml

test-update:
	pytest --snapshot-update