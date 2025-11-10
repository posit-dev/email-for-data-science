build-docs: generate-mjml-tags
	cd docs && uv run quartodoc build --verbose && quarto render

preview:
	cd docs && quarto preview

test:
	pytest nbmail/tests nbmail/mjml/tests nbmail/compose/tests --cov-report=xml

test-update:
	pytest nbmail/tests nbmail/mjml/tests nbmail/compose/tests --snapshot-update

generate-mjml-tags:
	python3 nbmail/mjml/scripts/generate_tags.py
