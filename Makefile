DJANGO_ADDRESS = $(or $(DJANGO_SERVE_ADDRESS), 127.0.0.1)
DJANGO_PORT = 9001
DJANGO_SETTINGS_MODULE = hypha.settings.dev
JS_VENDOR_DIR = ./hypha/static_src/javascript/vendor
JS_ESM_DIR = ./hypha/static_src/javascript/esm

# Check if uv is installed then use it, else fallback to pip
PIP := $(shell (command -v uv > /dev/null 2>&1 && echo "uv pip") || (command -v pip > /dev/null 2>&1 && echo "pip"))


.PHONY: help
help: ## Show this help menu with a list of available commands and their descriptions
	@echo "\nSpecify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-12s\033[m %s\n", $$1, $$2}'
	@echo ""


.PHONY: serve
serve: .cache/tandem .cache/py-packages .cache/dev-build-fe  ## Run Django server, docs preview, and watch frontend changes
	@.cache/tandem \
		'python manage.py runserver_plus $(DJANGO_ADDRESS):$(DJANGO_PORT) --settings=$(DJANGO_SETTINGS_MODULE)' \
		'npm:watch:*' \
		'mkdocs serve'

.PHONY: test
test: lint py-test cov-html  ## Run all tests (linting, Python tests) and generate coverage report


.PHONY: fmt
fmt: .cache/dev-build-fe  ## Run code formatters on all code using pre-commit
	@pre-commit run --all-files


.PHONY: lint
lint: .cache/dev-build-fe  ## Run all linters
	@echo "Running linters"
	@pre-commit run --all-files


.PHONY: py-test
py-test: .cache/py-packages  ## Run Python tests with pytest, including coverage report
	@echo "Running python tests"
	pytest --reuse-db --cov --cov-report term:skip-covered

	@echo "Removing test files generated during test"
	@find media/ -iname 'test_*.pdf' -o -iname 'test_image*' -o -iname '*.dat' -delete
	@find media/ -type d -empty -delete
	@rm -rf media/temp_uploads/*


.PHONY: cov-html
cov-html:  ## Generate HTML coverage report from previous test run
ifneq ("$(wildcard .coverage)","")
	@rm -rf htmlcov
	@echo "Generate html coverage report…"
	coverage html
	@echo "Open 'htmlcov/index.html' in your browser to see the report."
else
	$(error Unable to generate html coverage report, please run 'make test' or 'make py-test')
endif


.PHONY: download-esm-modules
download-esm-modules:  ## Download ECMAScript modules for the project
	$(PIP) install download-esm
	download-esm @github/relative-time-element $(JS_ESM_DIR)
	download-esm @github/filter-input-element $(JS_ESM_DIR)
	download-esm choices.js $(JS_ESM_DIR)


.cache/tandem:  ## Install tandem, a tool for running multiple commands in parallel
	@mkdir -p $$(dirname $@)
	@curl -fsSL https://raw.githubusercontent.com/rosszurowski/tandem/524b1e0379efca55bcf9ad2a9fe5453a117eb0a4/install.sh | bash -s -- --dest="$$(dirname $@)"


.cache/dev-build-fe: .cache/npm-packages $(shell find hypha/static_src)  ## Build frontend resources for development
	@mkdir -p $$(dirname $@)
	@.cache/tandem 'npm:dev:build:*'
	@touch $@


.cache/py-packages: requirements/dev.txt requirements/docs.txt  ## Install Python packages for development and documentation
	@mkdir -p $$(dirname $@)
	$(PIP) install --no-deps -r requirements/dev.txt -r requirements/docs.txt
	@touch $@


.cache/npm-packages: package.json  	## Install Node.js packages and copy JavaScript files to vendor directory
	@mkdir -p $$(dirname $@)
	NODE_ENV=development npm install
	cp node_modules/htmx.org/dist/htmx.min.js $(JS_VENDOR_DIR)/htmx.min.js
	cp node_modules/htmx.org/dist/ext/multi-swap.js $(JS_VENDOR_DIR)/htmx-ext-multi-swap.min.js
	cp node_modules/alpinejs/dist/cdn.min.js $(JS_VENDOR_DIR)/alpine.min.js
	cp node_modules/@alpinejs/focus/dist/cdn.min.js $(JS_VENDOR_DIR)/alpine-focus.min.js
	cp node_modules/daterangepicker/moment.min.js $(JS_VENDOR_DIR)/moment.min.js
	cp node_modules/daterangepicker/daterangepicker.js $(JS_VENDOR_DIR)/daterangepicker.min.js
	@touch $@
