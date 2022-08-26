.PHONY: help
help:
	@echo "Usage:"
	@echo "    make help             prints this help."
	@echo "    make lint             run all python linting."
	@echo "    make test             run all python linting and test"
	@echo "    make sort             run the isort import linter."
	@echo "    make sort-fix         fix import sort order."
	@echo "    make style            run the python code style linter."

.PHONY: lint
lint: sort style

.PHONY: sort
sort:
	@echo "Checking imports with isort" && isort --check-only --diff hypha

.PHONY: sort-fix
sort-fix:
	@echo "Fixing imports with isort" && isort hypha

.PHONY: style
style:
	@echo "Checking code style with flake8" && flake8 .

test: lint
	pytest --reuse-db --cov --cov-report term:skip-covered
	@rm -rf htmlcov
	coverage html
