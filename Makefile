.ONESHELL:

# Can be overridden to use a different directory name.
ifeq ($(VENV),)
  VENV := .venv
endif

# Can be overridden to use a different Python version.
ifeq ($(PYTHON_VERSION),)
  PYTHON_VERSION := 3.10
endif

# Can be overridden to pass flags to pytest, like `-k`.
ifeq ($(PYTEST_FLAGS),)
  PYTEST_FLAGS :=
endif

# Can be overridden to change what pyright command is run.
# This is used to switch between the pip and npm commands.
ifeq ($(PYRIGHT_MODE),)
  PYRIGHT_MODE := pip
endif

# Can be overridden to change whether packages in the repo
# will be installed from PyPI or the local filesystem.
ifeq ($(REWRITE_DEPENDENCIES),)
  REWRITE_DEPENDENCIES := true
endif

# Can be overridden.
ifeq ($(GITHUB_REF),)
  GITHUB_REF := 00000000-0000-0000-0000-000000000000
endif

# Can be overridden.
ifeq ($(GITHUB_WORKSPACE),)
  GITHUB_WORKSPACE := $(CURDIR)
endif

# Can be overridden. Use "pypi" to publish to production.
ifeq ($(PYPI_REPO),)
  PYPI_REPO := testpypi
endif


ACTIVATE_VENV := . $(VENV)/bin/activate

PACKAGE_INSTALL_DIR := $(VENV)/lib/python*/site-packages/BL_Python

# used to suppress outputs of targets (see `test` and `clean-test`)
CMD_PREFIX=

dev : venv filesystem-deps latest-pip
	$(ACTIVATE_VENV)

	pip install -e .[dev-dependencies]
#	By default, psycopg2 is not installed
#	but it should be for development
	pip install -e src/database[postgres-binary]

	rm -rf $(PACKAGE_INSTALL_DIR)
	@echo '\nActivate your venv with `. $(VENV)/bin/activate`'

cicd : venv filesystem-deps latest-pip
	$(ACTIVATE_VENV)

	pip install .[dev-dependencies]
#	By default, psycopg2 is not installed
#	but it should be for CI/CD
	pip install src/database[postgres-binary]

filesystem-deps : venv latest-pip
	$(ACTIVATE_VENV)

	pip install toml

	REWRITE_DEPENDENCIES=$(REWRITE_DEPENDENCIES) \
	GITHUB_REF=$(GITHUB_REF) \
	GITHUB_WORKSPACE=$(GITHUB_WORKSPACE) \
	./.github/workflows/CICD-scripts/pyproject_dependency_rewrite.py

latest-pip : venv
	$(ACTIVATE_VENV)

	pip install -U pip

venv :
	test -d $(VENV) || env python$(PYTHON_VERSION) -m venv $(VENV)

format-isort :
	$(ACTIVATE_VENV)

	isort src 

format-ruff :
	$(ACTIVATE_VENV)

	ruff format --preview --respect-gitignore

format : format-isort format-ruff

test-isort :
	$(ACTIVATE_VENV)

	isort --check-only src 

test-ruff :
	$(ACTIVATE_VENV)

	ruff format --preview --respect-gitignore --check

test-pyright :
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

test-pytest :
	$(ACTIVATE_VENV)

	pytest $(PYTEST_FLAGS)
	coverage html -d coverage


test : CMD_PREFIX=@
test : clean-test test-isort test-ruff test-pyright test-pytest

publish-all :
	$(ACTIVATE_VENV)

	./publish_all.sh $(PYPI_REPO)

clean-build :
	find . -type d \( \
		-name build \
		-o -name __pycache__ \
		-o -name \*.egg-info \
		-o -name .pytest-cache \
	\) -prune -exec rm -rf {} \;

clean-test :
	$(CMD_PREFIX)rm -rf cov.xml \
		pytest.xml \
		coverage \
		.coverage 

clean : clean-build clean-test
	rm -rf $(VENV)

	@echo '\nDeactivate your venv with `deactivate`'
