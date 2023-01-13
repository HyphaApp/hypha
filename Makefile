.PHONY: help
help:
	@echo "Usage:"
	@echo "    make help             prints this help."
	@echo "    make lint             run python linting."
	@echo "    make lint-fix         try fixing plausible python linting issues."
	@echo "    make test             run linting and test and generate html coverage report"
	@echo "    make py-test          run all python tests and display coverage"
	@echo "    make cov-html         generate html coverage report"
	@echo "    make serve-docs       run documentation development server."

.PHONY: lint
lint:
	@echo "Checking code style with ruff" && ruff .

lint-fix:
	@echo "Try fixing plausible python linting issues." && ruff --fix .

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

serve-docs:
	@echo "Serve and watch documentation locally:"
	mkdocs serve
