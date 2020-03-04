.PHONY: test clean clean-pyc run dev-run lint lint-syntax-errors test-log test-w-coverage lint-no-fail type-check

.DEFAULT: test

PYTHON = python3
PLATFORM := ${shell uname -o}
INVENV_PATH = ${shell which invenv}

${info Platform: ${PLATFORM}}
${info invenv: ${INVENV_PATH}}

ifeq (${VIRTUAL_ENV},)
  VENV_NAME = .venv
else
  VENV_NAME = ${VIRTUAL_ENV}
endif
${info Using ${VENV_NAME}}

VENV_BIN = ${VENV_NAME}/bin

ifeq (${INVENV_PATH},)
  INVENV = export VIRTUAL_ENV="${VENV_NAME}"; export PATH="${VENV_BIN}:${PATH}"; unset PYTHON_HOME;
else
  INVENV = invenv -C ${VENV_NAME}
endif

ifeq (${PLATFORM}, Android)
  FLAKE8_FLAGS = --jobs=1
else
  FLAKE8_FLAGS = --jobs=auto
endif

venv: ${VENV_NAME}/made

install: venv ${VENV_NAME}/req.installed
install-test: venv install ${VENV_NAME}/req-test.installed
install-dev: venv install-test ${VENV_NAME}/req-dev.installed
install-typecheck: venv install-test ${VENV_NAME}/req-typecheck.installed

${VENV_NAME}/made:
	test -d ${VENV_NAME} || ${PYTHON} -m venv ${VENV_NAME}
	${INVENV} pip install pip-tools
	@touch $@

${VENV_NAME}/req.installed: requirements.txt
	${INVENV} pip install -Ur $<
	@touch $@

${VENV_NAME}/req-test.installed: setup.py setup.cfg
	${INVENV} pip install -e .[test]
	@touch $@

${VENV_NAME}/req-dev.installed: setup.py setup.cfg
	${INVENV} pip install -e .[dev]
	@touch $@

${VENV_NAME}/req-typecheck.installed:
	${INVENV} pip install pytype
	@touch $@

run: install
	${INVENV} python run.py 8081

dev-run: install-dev
	${INVENV} python run.py dev

lint-syntax-errors: install-test
	${INVENV} flake8 karp5 setup.py run.py cli.py --count --select=E9,F63,F7,F82 --show-source --statistics ${FLAKE8_FLAGS}

test: install-test clean-pyc
	${INVENV} pytest -vv karp5/tests/unit_tests

test-w-coverage: install-test clean-pyc
	${INVENV} pytest -vv --cov-config=setup.cfg --cov=karp5 --cov-report=term-missing karp5/tests

test-log: install-test clean-pyc
	${INVENV} pytest --cov=karp5 --cov-report=term-missing karp5/tests > pytest.log

lint: install
	${INVENV} pylint --rcfile .pylintrc karp5 setup.py cli.py run.py

lint-no-fail: install
	${INVENV} pylint --rcfile .pylintrc --exit-zero karp5 setup.py cli.py run.py

type-check: install-test install-typecheck
	${INVENV} pytype karp5

clean: clean-build clean-pyc clean-test clean-venv

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	#rm -fr .tox/
	#rm -f .coverage
	#rm -fr htmlcov/
	rm -fr .pytest_cache

clean-venv:
	rm -rf ./{VENV_NAME}

bump-version-patch: install-dev
	${INVENV} bump2version patch

bump-version-minor: install-dev
	${INVENV} bump2version minor

bump-version-major: install-dev
	${INVENV} bump2version major
