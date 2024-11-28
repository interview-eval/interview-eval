.PHONY: style

check_dirs := interview-eval tests

style:
	uv run isort $(check_dirs)
	uv run black --line-length 119 --target-version py310 $(check_dirs)
