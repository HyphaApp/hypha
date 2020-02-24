.PHONY:
help:
	@echo "Usage:"
	@echo "    make help             prints this help."
	@echo "    make fix              fix import sort order."
	@echo "    make sort             run the linter."

.PHONY: fix
fix:
	isort -y

.PHONY: sort
sort:
	@echo "Running Isort" && isort --check-only --diff || exit 1
