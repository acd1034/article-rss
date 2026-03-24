MODULE_NAME = sample2

.PHONY: install
install:
	mv sample $(MODULE_NAME)
	sed -i '' 's/name = "sample"/name = "$(MODULE_NAME)"/g' pyproject.toml
	sed -i '' 's/from sample import square/from $(MODULE_NAME) import square/g' tests/test_square.py
	uv sync --extra dev
