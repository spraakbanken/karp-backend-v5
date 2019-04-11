default: test clean clean-pyc run dev-run

VENV_NAME = venv
PYTHON = ${VENV_NAME}/bin/python

venv: ${VENV_NAME}/made

install: venv ${VENV_NAME}/req.installed
install-dev: venv ${VENV_NAME}/req-dev.installed

${VENV_NAME}/made:
	test -d venv || virtualenv --python python2.7 venv
	${PYTHON} -m pip install pip-tools
	@touch $@

${VENV_NAME}/req.installed: requirements.txt
	${PYTHON} -m pip install -Ur $<
	@touch $@

${VENV_NAME}/req-dev.installed: setup.py
	${PYTHON} -m pip install -e .[dev]
	@touch $@

run: install
	${PYTHON} run.py 8081

dev-run: install-dev
	${PYTHON} run.py dev

test: venv-dev clean-pyc
	${PYTHON} -m pytest --cov=src --cov-report=term-missing tests

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm --force {} \;

prepare-release: venv setup.py
	. ./${VENV_NAME}/bin/activate; pip-compile

bump-version-patch:
	bumpversion patch
	make prepare-release

bump-version-minor:
	bumpversion minor
	make prepare-release

bump-version-major:
	bumpversion major
	make prepare-release
