.PHONY: help
help:
	@echo "Usage:"
	@echo "    make help             prints this help."
	@echo "    make lint             run all python linting."
	@echo "    make test             run linting and test and generate html coverage report"
	@echo "    make py-test          run all python tests and display coverage"
	@echo "    make cov-html         generate html coverage report"
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

.PHONY: cov-htmlcov
cov-html:
ifneq ("$(wildcard .coverage)","")
	@rm -rf htmlcov
	@echo "Generate html coverage report..." && coverage html
	@echo "Open 'htmlcov/index.html' in your browser to see the report."
else
	$(error Unable to generate html coverage report, please run 'make test' or 'make py-test')
endif

.PHONY: py-test
py-test:
	@echo "Running python tests"
	pytest --reuse-db --cov --cov-report term:skip-covered

.PHONY: test
test: lint py-test cov-html
