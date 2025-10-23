build-docs:
	cd docs && uv run quartodoc build --verbose && quarto render

preview:
	cd docs && quarto preview

test:
	pytest --cov-report=xml

test-update:
	pytest --snapshot-update

generate-mjml-tags:
	python3 scripts/generate-tags.py
