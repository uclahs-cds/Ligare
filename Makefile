.ONESHELL:

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


# Can be overridden. This is used to change the prereqs
# of some supporting targets, like `format-ruff`.
# This variable is reassigned to whichever of the dev/cicd
# targets actually runs.
DEFAULT_TARGET ?= dev
.DEFAULT_GOAL = $(DEFAULT_TARGET)


ifeq ($(DEFAULT_TARGET),dev)
    CONFIGURE_TARGET := _dev_configure
    BUILD_TARGET := _dev_build
else ifeq ($(DEFAULT_TARGET),cicd)
    CONFIGURE_TARGET := _cicd_configure
    BUILD_TARGET := _cicd_build
else
    $(error DEFAULT_TARGET must be one of "dev" or "cicd")
endif


ACTIVATE_VENV := . $(VENV)/bin/activate
REPORT_VENV_USAGE := echo '\nActivate your venv with `. $(VENV)/bin/activate`'

PACKAGE_INSTALL_DIR := $(VENV)/lib/python*/site-packages/BL_Python

# used to suppress outputs of targets (see `test` and `clean-test`)
CMD_PREFIX=

define package_to_dist
$(VENV)/lib/python$(PYTHON_VERSION)/site-packages/BL_Python.$(1)-*.dist-info
endef

define package_to_inst
$(VENV)/lib/python$(PYTHON_VERSION)/site-packages/BL_Python/$(1)/__init__.py
endef

define dep_to_venv_path
$(VENV)/lib/python$(PYTHON_VERSION)/site-packages/$(1)
endef

PYPROJECT_FILES=./pyproject.toml $(wildcard src/*/pyproject.toml)
PACKAGE_PATHS=$(subst /pyproject.toml,,$(PYPROJECT_FILES))
PACKAGES=$(subst /pyproject.toml,,$(subst src/,BL_Python.,$(wildcard src/*/pyproject.toml)))

.PHONY: dev
dev : $(VENV) $(SETUP_DEPENDENCIES)
	$(MAKE) _dev_build DEFAULT_TARGET=dev
_dev_configure : $(VENV) $(PYPROJECT_FILES)
_dev_build : _dev_configure
	@if [ -d $(call package_to_dist,all) ]; then
		echo "Package $@ is already built, skipping..."
	else
		$(ACTIVATE_VENV)

		pip install -e .[dev-dependencies]
#		By default, psycopg2 is not installed
#		but it should be for development
		pip install -e src/database[postgres-binary]

		rm -rf $(PACKAGE_INSTALL_DIR)
	fi

	@$(REPORT_VENV_USAGE)

cicd : $(VENV) $(SETUP_DEPENDENCIES)
	$(MAKE) _cicd_build DEFAULT_TARGET=cicd
_cicd_configure : $(VENV) $(PYPROJECT_FILES)
_cicd_build : _cicd_configure
	@if [ -f $(call package_to_inst,) ]; then
		echo "Package is already built, skipping..."
	else
		$(ACTIVATE_VENV)

		pip install .[dev-dependencies]
#		By default, psycopg2 is not installed
#		but it should be for CI/CD
		pip install src/database[postgres-binary]
	fi

	@$(REPORT_VENV_USAGE)

$(PACKAGES) : BL_Python.%: src/%/pyproject.toml $(VENV) $(CONFIGURE_TARGET) $(PYPROJECT_FILES)
	@if [ -d $(call package_to_dist,$*) ]; then
		@echo "Package $@ is already built, skipping..."
	else
		$(ACTIVATE_VENV)

		if [ "$@" = "BL_Python.database" ]; then
			pip install -e $(dir $<)[postgres-binary]
		else
			pip install -e $(dir $<)
		fi

		rm -rf $(PACKAGE_INSTALL_DIR)
	fi

	@$(REPORT_VENV_USAGE)


SETUP_DEPENDENCIES=$(call dep_to_venv_path,toml/__init__.py) $(call dep_to_venv_path,typing_extensions.py)
 $(call dep_to_venv_path,toml/__init__.py): $(VENV)
	$(ACTIVATE_VENV)

	pip install toml

 $(call dep_to_venv_path,typing_extensions.py): $(VENV)
	$(ACTIVATE_VENV)

	pip install typing_extensions

$(PACKAGE_PATHS) : $(VENV) $(SETUP_DEPENDENCIES)
$(PYPROJECT_FILES) : $(VENV) $(SETUP_DEPENDENCIES)
	$(ACTIVATE_VENV)

	REWRITE_DEPENDENCIES=$(REWRITE_DEPENDENCIES) \
	GITHUB_REF=$(GITHUB_REF) \
	GITHUB_WORKSPACE=$(GITHUB_WORKSPACE) \
	./.github/workflows/CICD-scripts/pyproject_dependency_rewrite.py -c $@


$(VENV) :
	test -d $(VENV) || env python$(PYTHON_VERSION) -m venv $(VENV)

	$(ACTIVATE_VENV)

	pip install -U pip


format-isort : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV)

	isort src

format-ruff : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV)

	ruff format --preview --respect-gitignore

.PHONY: format format-ruff format-isort
format : $(VENV) $(BUILD_TARGET) format-isort format-ruff


test-isort : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV)

	isort --check-only src

test-ruff : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV)

	ruff format --preview --respect-gitignore --check

test-pyright : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV)

  ifeq "$(PYRIGHT_MODE)" "pip"
	pyright
  else
  ifeq "$(PYRIGHT_MODE)" "npm"
#	this isn't the real install path everywhere,
#	but this is used for CI/CD
	./node_modules/bin/pyright
  else
	@echo "Invalid PYRIGHT_MODE '$(PYRIGHT_MODE)'"
	@exit 1
  endif
  endif

test-bandit : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV)

#	don't exit with an error
#	while testing bandit.
	-bandit -c pyproject.toml \
		--format sarif \
		--output $(REPORTS_DIR)/$(BANDIT_REPORT) \
		-r .

test-pytest : $(VENV) $(BUILD_TARGET)
	$(ACTIVATE_VENV)

	pytest $(PYTEST_FLAGS) \
		&& PYTEST_EXIT_CODE=0 \
		|| PYTEST_EXIT_CODE=$$?

	-coverage html --data-file=$(REPORTS_DIR)/$(PYTEST_REPORT)/.coverage
	-junit2html $(REPORTS_DIR)/$(PYTEST_REPORT)/pytest.xml $(REPORTS_DIR)/$(PYTEST_REPORT)/pytest.html

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
	$(ACTIVATE_VENV)

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
	\) -prune -exec rm -rf {} \;

clean-test :
	$(CMD_PREFIX)rm -rf \
		$(REPORTS_DIR)/$(PYTEST_REPORT) \
		$(REPORTS_DIR)/$(BANDIT_REPORT)

.PHONY: clean clean-test clean-build
clean : clean-build clean-test
	rm -rf $(VENV)

	@echo '\nDeactivate your venv with `deactivate`'

.PHONY: remake
remake :
	$(MAKE) clean
	$(MAKE)

reset-check:
#	https://stackoverflow.com/a/47839479
	@echo -n "This will make destructive changes! Considering stashing changes first.\n"
	@( read -p "Are you sure? [y/N]: " response && case "$$response" in [yY]) true;; *) false;; esac )

.PHONY: reset reset-check
reset : reset-check clean
	git checkout -- $(PYPROJECT_FILES)
