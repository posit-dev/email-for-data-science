build-docs: generate-mjml-tags
	cd docs && uv run quartodoc build --verbose && quarto render

preview:
	cd docs && quarto preview

test:
	pytest emailer_lib/tests emailer_lib/mjml/tests --cov-report=xml

test-update:
	pytest emailer_lib/tests emailer_lib/mjml/tests --snapshot-update

generate-mjml-tags:
	python3 emailer_lib/mjml/scripts/generate_tags.py
