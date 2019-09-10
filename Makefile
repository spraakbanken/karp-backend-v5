default: test clean clean-pyc

VENV_NAME = venv3
PYTHON = ${VENV_NAME}/bin/python

venv: ${VENV_NAME}/made

install-dev: venv ${VENV_NAME}/req-dev.installed
install: venv ${VENV_NAME}/req.installed

${VENV_NAME}/made:
	test -d ${VENV_NAME} || python -m venv ${VENV_NAME}
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

test: install-dev clean-pyc
	${PYTHON} -m pytest --cov=src --cov-report=term-missing tests
	# ${PYTHON} -m pytest tests

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
