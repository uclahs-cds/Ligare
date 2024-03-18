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


# Can be overridden. This is used to change the prereqs
# of some supporting targets, like `format-ruff`.
# This variable is reassigned to whichever of the dev/cicd
# targets actually runs.
DEFAULT_TARGET ?= dev
.DEFAULT_GOAL = $(DEFAULT_TARGET)

define assign_default_target
    DEFAULT_TARGET := $(1)
endef

ifeq ($(DEFAULT_TARGET),dev)
else ifeq ($(DEFAULT_TARGET),cicd)
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
PACKAGES=BL_Python.all $(subst /pyproject.toml,,$(subst src/,BL_Python.,$(wildcard src/*/pyproject.toml)))

# Rather than duplicating BL_Python.all,
# just prereq it.
.PHONY: dev
dev : dev_mode BL_Python.all

.PHONY: cicd
cicd : cicd_mode $(VENV) $(PYPROJECT_FILES)
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

MODES=dev_mode cicd_mode
# Used to force DEFAULT_TARGET to whatever
# the actual .DEFAULT_GOAL is.
$(MODES):
	@echo $(call assign_default_target,$(subst _mode,,$@))


# BL_Python.all does not have a src/%/pyproject.toml
# prereq because its pyproject.toml is at /
BL_Python.all: $(VENV) $(PYPROJECT_FILES)
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

$(filter-out BL_Python.all, $(PACKAGES)): BL_Python.%: src/%/pyproject.toml $(VENV)
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


format-isort : $(VENV) $(DEFAULT_TARGET)
	$(ACTIVATE_VENV)

	isort src 

format-ruff : $(VENV) $(DEFAULT_TARGET)
	$(ACTIVATE_VENV)

	ruff format --preview --respect-gitignore

.PHONY: format format-ruff format-isort
format : $(VENV) $(DEFAULT_TARGET) format-isort format-ruff


test-isort : $(VENV) $(DEFAULT_TARGET)
	$(ACTIVATE_VENV)

	isort --check-only src 

test-ruff : $(VENV) $(DEFAULT_TARGET)
	$(ACTIVATE_VENV)

	ruff format --preview --respect-gitignore --check

test-pyright : $(VENV) $(DEFAULT_TARGET)
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

test-pytest : $(VENV) $(DEFAULT_TARGET)
	$(ACTIVATE_VENV)

	pytest $(PYTEST_FLAGS)
	coverage html --data-file=$(REPORTS_DIR)/pytest/.coverage

.PHONY: test test-pytest test-pyright test-ruff test-isort
_test : $(VENV) $(DEFAULT_TARGET) test-isort test-ruff test-pyright test-pytest
test : CMD_PREFIX=@
test : clean-test
	$(MAKE) -j --keep-going _test


# Publishing should use a real install, which `cicd` fulfills
.PHONY: publish-all
publish-all : REWRITE_DEPENDENCIES=false
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
		$(REPORTS_DIR)/pytest

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
