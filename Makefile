DJANGO_PORT = 9001
JS_VENDOR_DIR = ./hypha/static_src/javascript/vendor
JS_ESM_DIR = ./hypha/static_src/javascript/esm


.PHONY: help
help: ## Show this help
	@echo "\nSpecify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-12s\033[m %s\n", $$1, $$2}'
	@echo ""


.PHONY: serve
serve: .cache/tandem build  ## Run Django and docs preview server, also watch and compile frontend changes
	@.cache/tandem \
		'python manage.py runserver 0.0.0.0:$(DJANGO_PORT) --settings=hypha.settings.dev' \
		'npm:watch:*' \
		'mkdocs serve'


.PHONY: build
build:  ## Build js and css resources for development
	@echo "Build js and css resources for development."
	npm run dev:build


.PHONY: fmt
fmt:  ## Run code formatters on all code
	@echo "run code formatters on all code."
	python -m ruff check --fix .
	python -m ruff format .
	npx prettier . --write
	djhtml hypha/

.PHONY: cov-html
cov-html:  ## Generate html coverage report
ifneq ("$(wildcard .coverage)","")
	@rm -rf htmlcov
	@echo "Generate html coverage report…"
	coverage html
	@echo "Open 'htmlcov/index.html' in your browser to see the report."
else
	$(error Unable to generate html coverage report, please run 'make test' or 'make py-test')
endif


.PHONY: lint
lint:  ## Run all linters
	@echo "Checking python code style with ruff"
	ruff check .
	ruff format --check .
	@echo "Checking html file indendation."
	djhtml hypha/ --check
	@echo "Checking js and css code style."
	npm run lint


.PHONY: lint-fix
lint-fix:  ## Fix all possible linter issues
	@echo "Try fixing plausible python linting issues."
	ruff check --fix .


.PHONY: py-test
py-test:  ## Run python tests
	@echo "Running python tests"
	pytest --reuse-db --cov --cov-report term:skip-covered


.PHONY: serve-django
serve-django:  ## Run Django server
	python manage.py runserver 0.0.0.0:$(DJANGO_PORT) --settings=hypha.settings.dev


.PHONY: clean-test-files
clean-test-files:
	@echo "Removing test files generated during test"
	find media/ -iname 'test_*.pdf' -delete
	find media/ -iname 'test_image*' -delete
	find media/ -iname '*.dat' -delete
	find media/ -type d -empty -delete
	rm -rf media/temp_uploads/*


.PHONY: test
test: lint py-test cov-html clean-test-files  ## Run all tests


.PHONY: watch
watch: build ## Watch js and css resources for development
	@echo "Watch js and css resources for development."
	npm run watch


.PHONY: download-esm-modules
download-esm-modules:  ## Download ESM modules
	pip install download-esm
	download-esm @github/relative-time-element $(JS_ESM_DIR)
	download-esm @github/filter-input-element $(JS_ESM_DIR)
	download-esm choices.js $(JS_ESM_DIR)


.PHONY: copy-npm-scripts
copy-npm-scripts:  ## Copy npm scripts
	# Used by "npm install"
	cp node_modules/htmx.org/dist/htmx.min.js $(JS_VENDOR_DIR)/htmx.min.js
	cp node_modules/htmx.org/dist/ext/multi-swap.js $(JS_VENDOR_DIR)/htmx-ext-multi-swap.min.js
	cp node_modules/alpinejs/dist/cdn.min.js $(JS_VENDOR_DIR)/alpine.min.js
	cp node_modules/@alpinejs/focus/dist/cdn.min.js $(JS_VENDOR_DIR)/alpine-focus.min.js
	cp node_modules/daterangepicker/moment.min.js $(JS_VENDOR_DIR)/moment.min.js
	cp node_modules/daterangepicker/daterangepicker.js $(JS_VENDOR_DIR)/daterangepicker.min.js


.cache/tandem:
	@mkdir -p $$(dirname $@)
	@curl -fsSL https://raw.githubusercontent.com/rosszurowski/tandem/main/install.sh | bash -s -- --dest="$$(dirname $@)"
