default: test

venv: venv/made

venv-dev: venv venv/made-dev

venv/made: requirements.txt
	test -d venv || virtualenv --python python2.7 venv
	. ./venv/bin/activate; pip install pip-tools; pip install -Ur $<
	touch $@

venv/made-dev: setup.py
	. ./venv/bin/activate; pip install -e .[dev]
	touch $@

dev-run: venv
	. ./venv/bin/activate; python run.py 8081

test: venv-dev
	. ./venv/bin/activate; py.test tests

prepare-release: venv setup.py
	. ./venv/bin/activate; pip-compile

bump-version-patch:
	bumpversion patch
	make prepare-release

bump-version-minor:
	bumpversion minor
	make prepare-release

bump-version-major:
	bumpversion major
	make prepare-release
