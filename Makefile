.PHONY: test clean clean-pyc run dev-run lint lint-syntax-errors test-log

.DEFAULT: test

PYTHON = python3
PLATFORM := ${shell uname -o}

${info Platform: ${PLATFORM}}
ifeq (${VIRTUAL_ENV},)
  VENV_NAME = .venv
  VENV_BIN = ${VENV_NAME}/bin
else
  VENV_NAME = ${VIRTUAL_ENV}
  VENV_BIN = ${VENV_NAME}/bin
endif
${info Using ${VENV_NAME}}

ifeq (${VIRTUAL_ENV},)
  VENV_ACTIVATE = . ${VENV_BIN}/activate
else
  VENV_ACTIVATE = true
endif

ifeq (${PLATFORM}, Android)
  FLAKE8_FLAGS = --jobs=1
else
  FLAKE8_FLAGS = --jobs=auto
endif

venv: ${VENV_NAME}/made

install: venv ${VENV_NAME}/req.installed
install-dev: venv ${VENV_NAME}/req-dev.installed

${VENV_NAME}/made:
	test -d ${VENV_NAME} || ${PYTHON} -m venv ${VENV_NAME}
	${VENV_ACTIVATE}; pip install pip-tools
	@touch $@

${VENV_NAME}/req.installed: requirements.txt
	${VENV_ACTIVATE}; pip install -Ur $<
	@touch $@

${VENV_NAME}/req-dev.installed: setup.py
	${VENV_ACTIVATE}; pip install -e .[dev]
	@touch $@

run: install
	${VENV_ACTIVATE}; python run.py 8081

dev-run: install-dev
	${VENV_ACTIVATE}; python run.py dev

lint-syntax-errors: install-dev
	${VENV_ACTIVATE}; flake8 karp5 setup.py run.py cli.py --count --select=E9,F63,F7,F82 --show-source --statistics ${FLAKE8_FLAGS}

test: install-dev clean-pyc lint-syntax-errors
	${VENV_ACTIVATE}; pytest -vv --cov=karp5 --cov-report=term-missing karp5/tests

test-log: install-dev clean-pyc
	${VENV_ACTIVATE}; pytest --cov=karp5 --cov-report=term-missing karp5/tests > pytest.log

lint: install-dev
	${VENV_ACTIVATE}; pylint --rcfile .pylintrc karp5 setup.py cli.py run.py

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm --force {} \;

prepare-release: venv setup.py
	${VENV_ACTIVATE}; pip-compile --output-file=requirements.txt setup.py

bump-version-patch:
	bumpversion patch
	make prepare-release

bump-version-minor:
	bumpversion minor
	make prepare-release

bump-version-major:
	bumpversion major
	make prepare-release
