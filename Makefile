.phony: test clean clean-pyc run dev-run

.default: test

ifeq (${VIRTUAL_ENV},)
  VENV_NAME = venv
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

PYTHON = ${VENV_BIN}/python

venv: ${VENV_NAME}/made

install: venv ${VENV_NAME}/req.installed
install-dev: venv ${VENV_NAME}/req-dev.installed

${VENV_NAME}/made:
	test -d ${VENV_NAME} || virtualenv --python python2.7 ${VENV_NAME}
	${VENV_ACTIVATE}; pip install pip-tools
	@touch $@

${VENV_NAME}/req.installed: requirements.txt
	${VENV_ACTIVATE}; pip install -Ur $<
	@touch $@

${VENV_NAME}/req-dev.installed: setup.py
	${VENV_ACTIVATE}; pip install -e .[dev]
	@touch $@

run: install
	${PYTHON} run.py 8081

dev-run: install-dev
	${PYTHON} run.py dev

test: install-dev clean-pyc
	${VENV_ACTIVATE}; pytest --cov=src --cov-report=term-missing tests

test-log: install-dev clean-pyc
	${VENV_ACTIVATE}; pytest --cov=src --cov-report=term-missing tests > pytest.log

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
