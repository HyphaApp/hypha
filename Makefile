DJANGO_PORT = 9001
JS_VENDOR_DIR = ./hypha/static_src/src/javascript/vendor
CSS_VENDOR_DIR = ./hypha/static_src/src/javascript/vendor
JS_ESM_DIR = ./hypha/static_src/src/javascript/esm

.PHONY: help
help:
	@echo "Usage:"
	@echo "  make help               prints this help."
	@echo "  make build              build js and css resources for development"
	@echo "  make cov-html           generate html coverage report"
	@echo "  make lint               run css, js and python linting."
	@echo "  make fmt                run code formatters on all code."
	@echo "  make lint-fix           try fixing plausible python linting issues."
	@echo "  make py-test            run all python tests and display coverage"
	@echo "  make test               run linting and test and generate html coverage report"
	@echo "  make serve-docs         run documentation development server"
	@echo "  make serve-django       run Django development server on port 9001."
	@echo "  make serve              run Django and docs preview server, also watch and compile frontend changes"
	@echo "  make watch              watch js and css resources for development"
	@echo "  make download-esm-modules  download esm modules from npm and copy to static_src"

.PHONY: serve
serve:
	$(MAKE) -j3 watch serve-django serve-docs

.PHONY: build
build:
	@echo "Build js and css resources for development."
	npm run dev:build

.PHONY: fmt
fmt:
	@echo "run code formatters on all code."
	python -m ruff --fix .
	python -m ruff format .
	npx prettier . --write
	djhtml hypha/

.PHONY: cov-html
cov-html:
ifneq ("$(wildcard .coverage)","")
	@rm -rf htmlcov
	@echo "Generate html coverage report…"
	coverage html
	@echo "Open 'htmlcov/index.html' in your browser to see the report."
else
	$(error Unable to generate html coverage report, please run 'make test' or 'make py-test')
endif

.PHONY: lint
lint:
	@echo "Checking python code style with ruff"
	ruff check .
	ruff format --check .
	@echo "Checking html file indendation."
	djhtml hypha/ --check
	@echo "Checking js and css code style."
	npm run lint


.PHONY: lint-fix
lint-fix:
	@echo "Try fixing plausible python linting issues."
	ruff --fix .

.PHONY: py-test
py-test:
	@echo "Running python tests"
	pytest --reuse-db --cov --cov-report term:skip-covered

.PHONY: serve-django
serve-django:
	python manage.py runserver 0.0.0.0:$(DJANGO_PORT) --settings=hypha.settings.dev

.PHONY: test
test: lint py-test cov-html

.PHONY: serve-docs
serve-docs:
	@echo "Serve and watch documentation locally:"
	mkdocs serve

.PHONY: watch
watch:
	@echo "Watch js and css resources for development."
	npm run watch

.PHONY: download-esm-modules
download-esm-modules:
	pip install download-esm
	download-esm @github/relative-time-element $(JS_ESM_DIR)
	download-esm @github/filter-input-element $(JS_ESM_DIR)
	download-esm choices.js $(JS_ESM_DIR)

.PHONY: copy-npm-scripts
copy-npm-scripts:
	# Used by "npm install"
	cp node_modules/htmx.org/dist/htmx.min.js $(JS_VENDOR_DIR)/htmx.min.js
	cp node_modules/htmx.org/dist/ext/multi-swap.js $(JS_VENDOR_DIR)/htmx-ext-multi-swap.min.js
	cp node_modules/alpinejs/dist/cdn.min.js $(JS_VENDOR_DIR)/alpine.min.js
	cp node_modules/@alpinejs/focus/dist/cdn.min.js $(JS_VENDOR_DIR)/alpine-focus.min.js
	cp node_modules/daterangepicker/moment.min.js $(JS_VENDOR_DIR)/moment.min.js
	cp node_modules/daterangepicker/daterangepicker.js $(JS_VENDOR_DIR)/daterangepicker.min.js
