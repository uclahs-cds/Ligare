# Can be overridden to use a different directory name.
VENV ?= .venv

# Can be overridden to use a different Python version.
PYTHON_VERSION ?= 3.10

# Can be overridden to pass flags to pytest, like `-k`.
PYTEST_FLAGS ?=

# Can be overridden to change what pyright command is run.
# This is used to switch between the pip and npm commands.
PYRIGHT_MODE ?= pip

# Can be overridden to change whether packages in the repo
# will be installed from PyPI or the local filesystem.
REWRITE_DEPENDENCIES ?= true

# Can be overridden.
GITHUB_REF ?= 00000000-0000-0000-0000-000000000000

# Can be overridden.
GITHUB_WORKSPACE ?= $(CURDIR)

# What repository to publish packages to.
# `testpypi` and `pypi` are valid values.
PYPI_REPO ?= testpypi

# The directory to write ephermal reports to,
# such as pytest coverage reports.
REPORTS_DIR ?= reports
BANDIT_REPORT := bandit.sarif
PYTEST_REPORT := pytest
PYTEST_TARGET ?= .
TOX_DIR := .tox


# Can be overridden. This is used to change the prereqs
# of some supporting targets, like `format-ruff`.
# This variable is reassigned to whichever of the dev/cicd
# targets actually runs.
DEFAULT_TARGET ?= dev
.DEFAULT_GOAL := $(DEFAULT_TARGET)

ACTIVATE_VENV := . $(VENV)/bin/activate
REPORT_VENV_USAGE := echo '\nActivate your venv with `. $(VENV)/bin/activate`'

PACKAGE_INSTALL_DIR := $(VENV)/lib/python*/site-packages/Ligare

# used to suppress outputs of targets (see `test` and `clean-test`)
CMD_PREFIX=

PYPROJECT_FILES=./pyproject.toml $(wildcard src/*/pyproject.toml)
PACKAGE_PATHS=$(subst /pyproject.toml,,$(PYPROJECT_FILES))
PACKAGES=$(subst /pyproject.toml,,$(subst src/,Ligare.,$(wildcard src/*/pyproject.toml)))


MAKE_ARTIFACT_DIRECTORY = .make
$(MAKE_ARTIFACT_DIRECTORY):
	mkdir -p $(MAKE_ARTIFACT_DIRECTORY)

SETUP_DEPENDENCIES_SENTINEL = $(MAKE_ARTIFACT_DIRECTORY)/dependencies_sentinel
SETUP_DEV_SENTINEL = $(MAKE_ARTIFACT_DIRECTORY)/setup_dev_sentinel
SETUP_CICD_SENTINEL = $(MAKE_ARTIFACT_DIRECTORY)/setup_cicd_sentinel
PYPROJECT_FILES_SENTINEL = $(MAKE_ARTIFACT_DIRECTORY)/pyproject_sentinel

ifeq ($(DEFAULT_TARGET),dev)
    BUILD_TARGET := $(SETUP_DEV_SENTINEL)
else ifeq ($(DEFAULT_TARGET),cicd)
    BUILD_TARGET := $(SETUP_CICD_SENTINEL)
else
    $(error DEFAULT_TARGET must be one of "dev" or "cicd")
endif


$(PYPROJECT_FILES_SENTINEL): $(VENV)
	$(MAKE) $(PYPROJECT_FILES)
	touch $@

.PHONY: dev
dev :
	$(MAKE) $(SETUP_DEV_SENTINEL) DEFAULT_TARGET=dev
# By default, psycopg2 is not installed
# but it should be for development
$(SETUP_DEV_SENTINEL): $(VENV) $(SETUP_DEPENDENCIES_SENTINEL) $(PYPROJECT_FILES_SENTINEL) | $(MAKE_ARTIFACT_DIRECTORY)
# `pip list` is multiple seconds faster than `pip show` ...
	$(ACTIVATE_VENV) && \
	if pip list -l --no-index | grep '^Ligare\.all\s'; then \
		echo "Package Ligare.all is already built, skipping..."; \
	else \
		pip install -e .[dev-dependencies] && \
		pip install -e src/database[postgres-binary] && \
		rm -rf $(PACKAGE_INSTALL_DIR); \
	fi
	touch $@
	@$(REPORT_VENV_USAGE)

.PHONY: cicd
cicd :
	$(MAKE) $(SETUP_CICD_SENTINEL) DEFAULT_TARGET=cicd
$(SETUP_CICD_SENTINEL): $(VENV) $(SETUP_DEPENDENCIES_SENTINEL) $(PYPROJECT_FILES_SENTINEL) | $(MAKE_ARTIFACT_DIRECTORY)
# `pip list` is multiple seconds faster than `pip show` ...
	$(ACTIVATE_VENV) && \
	if pip list -l --no-index | grep '^Ligare\.all\s'; then \
		echo "Package Ligare.all is already built, skipping..."; \
	else \
		pip install .[dev-dependencies] && \
		pip install src/database[postgres-binary]; \
	fi
	touch $@
	@$(REPORT_VENV_USAGE)

.PHONY: Ligare.all $(PACKAGES)
Ligare.all: $(DEFAULT_TARGET)
$(PACKAGES) : Ligare.%: src/%/pyproject.toml $(VENV) $(PYPROJECT_FILES_SENTINEL) | $(MAKE_ARTIFACT_DIRECTORY)
# `pip list` is multiple seconds faster than `pip show` ...
	$(ACTIVATE_VENV) && \
	if pip list -l --no-index | grep '^Ligare\.$*\s'; then \
		echo "Package $* is already built, skipping..."; \
	else \
		if [ "$@" = "Ligare.database" ]; then \
			pip install -e $(dir $<)[postgres-binary]; \
		else \
			pip install -e $(dir $<); \
		fi; \
		rm -rf $(PACKAGE_INSTALL_DIR); \
	fi
	@$(REPORT_VENV_USAGE)

$(SETUP_DEPENDENCIES_SENTINEL): $(VENV) | $(MAKE_ARTIFACT_DIRECTORY)
	$(ACTIVATE_VENV) && \
	if ! pip list -l --no-index | grep '^toml$*\s'; then \
		pip install toml; \
	fi

	$(ACTIVATE_VENV) && \
	if ! pip list -l --no-index | grep '^typing_extensions$*\s'; then \
		pip install typing_extensions; \
	fi

	touch $@

$(PACKAGE_PATHS) : $(VENV) $(SETUP_DEPENDENCIES_SENTINEL)
$(PYPROJECT_FILES) : $(VENV) $(SETUP_DEPENDENCIES_SENTINEL)
	$(ACTIVATE_VENV) && \
	REWRITE_DEPENDENCIES=$(REWRITE_DEPENDENCIES) \
	GITHUB_REF=$(GITHUB_REF) \
	GITHUB_WORKSPACE=$(GITHUB_WORKSPACE) \
	./.github/workflows/CICD-scripts/pyproject_dependency_rewrite.py -c $@

$(VENV) :
	test -d $(VENV) || env python$(PYTHON_VERSION) -m venv $(VENV)
	$(ACTIVATE_VENV) && \
	pip install -U pip

format-isort : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV) && \
	isort src

format-ruff : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV) && \
	ruff format --preview --respect-gitignore

.PHONY: format format-ruff format-isort
format : $(VENV) $(BUILD_TARGET) format-isort format-ruff

test-isort : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV) && \
	isort --check-only src

test-ruff : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV) && \
	ruff format --preview --respect-gitignore --check

test-pyright : $(VENV) $(BUILD_TARGET)
ifeq ($(PYRIGHT_MODE),pip)
	$(ACTIVATE_VENV) && \
	pyright
else ifeq ($(PYRIGHT_MODE),npm)
# this isn't the real install path everywhere,
# but this is used for CI/CD
	$(ACTIVATE_VENV) && \
	./node_modules/bin/pyright
else
	@echo "Invalid PYRIGHT_MODE '$(PYRIGHT_MODE)'"; \
	exit 1
endif

# don't exit with an error
# while testing bandit.
test-bandit : $(VENV) $(BUILD_TARGET)
	-$(ACTIVATE_VENV) && \
	bandit -c pyproject.toml \
		--format sarif \
		--output $(REPORTS_DIR)/$(BANDIT_REPORT) \
		-r .

test-pytest : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV) && \
	PYTEST_TARGET=$(PYTEST_TARGET) tox && PYTEST_EXIT_CODE=0 || PYTEST_EXIT_CODE=$$?; \
	coverage html --data-file=$(REPORTS_DIR)/$(PYTEST_REPORT)/.coverage; \
	junit2html $(REPORTS_DIR)/$(PYTEST_REPORT)/pytest.xml $(REPORTS_DIR)/$(PYTEST_REPORT)/pytest.html && \
	exit $$PYTEST_EXIT_CODE

.PHONY: test test-pytest test-bandit test-pyright test-ruff test-isort
_test : $(VENV) $(BUILD_TARGET) test-isort test-ruff test-pyright test-bandit test-pytest
test : CMD_PREFIX=@
test : clean-test
	$(MAKE) -j --keep-going _test

.PHONY: publish-all
# Publishing should use a real install, which `cicd` fulfills
publish-all : REWRITE_DEPENDENCIES=false
# Publishing should use a real install. Reset the build env.
publish-all : reset $(VENV)
	$(ACTIVATE_VENV) && \
	./publish_all.sh $(PYPI_REPO)

clean-build :
	find . -type d \
	\( \
		-path ./$(VENV) \
		-o -path ./.git \
	\) -prune -false \
	-o \( \
		-name build \
		-o -name dist \
		-o -name __pycache__ \
		-o -name \*.egg-info \
		-o -name .pytest-cache \
	\) -prune -exec rm -rf {} +

clean-test :
	$(CMD_PREFIX)rm -rf \
		$(TOX_DIR) \
		$(REPORTS_DIR)/$(PYTEST_REPORT) \
		$(REPORTS_DIR)/$(BANDIT_REPORT)

.PHONY: clean clean-test clean-build
clean : clean-build clean-test
	rm -rf $(VENV)
	rm -rf $(MAKE_ARTIFACT_DIRECTORY)
	rm -f  $(PYPROJECT_FILES_SENTINEL)
	@echo '\nDeactivate your venv with `deactivate`'

.PHONY: remake
remake :
	$(MAKE) clean
	$(MAKE)

reset-check:
# https://stackoverflow.com/a/47839479
	@echo -n "This will make destructive changes! Considering stashing changes first.\n"
	@( read -p "Are you sure? [y/N]: " response && case "$$response" in [yY]) true;; *) false;; esac )

.PHONY: reset reset-check
reset : reset-check clean
	git checkout -- $(PYPROJECT_FILES)


SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

Sphinx-help: $(VENV) $(DEFAULT_TARGET)
	@$(ACTIVATE_VENV) && \
	$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: Sphinx-help Makefile

Sphinx: $(VENV) $(DEFAULT_TARGET) Makefile
	$(MAKE) Sphinx-html

Sphinx-%: $(VENV) $(DEFAULT_TARGET) Makefile
	$(ACTIVATE_VENV) && \
	$(SPHINXBUILD) -M $(patsubst Sphinx-%,%,$@) "sphinx-docs/$(SOURCEDIR)" "sphinx-docs/$(BUILDDIR)" $(SPHINXOPTS)
