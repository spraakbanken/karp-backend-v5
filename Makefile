.phony: test clean clean-pyc run dev-run

<<<<<<< HEAD
.default: test

ifeq (${VIRTUAL_ENV},)
  VENV_NAME = venv3
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

=======
VENV_NAME = venv3
PYTHON = ${VENV_NAME}/bin/python

venv: ${VENV_NAME}/made

install-dev: venv ${VENV_NAME}/req-dev.installed
install: venv ${VENV_NAME}/req.installed

${VENV_NAME}/made:
	test -d venv || python -m venv venv
	${PYTHON} -m pip install pip-tools
	@touch $@

${VENV_NAME}/req.installed: requirements.txt
	${PYTHON} -m pip install -Ur $<
	@touch $@

${VENV_NAME}/req-dev.installed: setup.py
	${PYTHON} -m pip install -e .[dev]
	@touch $@

>>>>>>> 7fc39b18b9448f72d733c9c4fc3e671128ecd3ce
run: install
	${PYTHON} run.py 8081

dev-run: install-dev
	${PYTHON} run.py dev

test: install-dev clean-pyc
<<<<<<< HEAD
<<<<<<< HEAD
	${VENV_ACTIVATE}; pytest --cov=src --cov-report=term-missing tests

test-log: install-dev clean-pyc
	${VENV_ACTIVATE}; pytest --cov=src --cov-report=term-missing tests > pytest.log
=======
	${PYTHON} -m pytest --cov=src --cov-report=term-missing tests
	# ${PYTHON} -m pytest tests
>>>>>>> update makefile
=======
	${PYTHON} -m pytest --cov=src --cov-report=term-missing tests
	# ${PYTHON} -m pytest tests
>>>>>>> 7fc39b18b9448f72d733c9c4fc3e671128ecd3ce

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm --force {} \;

prepare-release: venv setup.py
<<<<<<< HEAD
<<<<<<< HEAD
	${VENV_ACTIVATE}; pip-compile --output-file=requirements.txt setup.py
=======
	. ./${VENV_NAME}/bin/activate; pip-compile
>>>>>>> update makefile
=======
	. ./${VENV_NAME}/bin/activate; pip-compile
>>>>>>> 7fc39b18b9448f72d733c9c4fc3e671128ecd3ce

bump-version-patch:
	bumpversion patch
	make prepare-release

bump-version-minor:
	bumpversion minor
	make prepare-release

bump-version-major:
	bumpversion major
	make prepare-release
