default: test clean clean-pyc

venv: venv/made

install-dev: venv venv/req-dev.installed
install: venv venv/req.installed

venv/made:
	test -d venv || python -m venv venv
	venv/bin/python -m pip install pip-tools
	touch $@

venv/req.installed: requirements.txt
	venv/bin/python -m pip install -Ur $<
	touch $@

run: venv
	venv/bin/python run.py 8081

dev-run: venv-dev
	venv/bin/python run.py dev

test: venv-dev clean-pyc
	./venv/bin/pytest --cov=src --cov-report=term-missing tests

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm --force {} \;

prepare-release: venv setup.py
	venv/bin/activate; pip-compile

bump-version-patch:
	bumpversion patch
	make prepare-release

bump-version-minor:
	bumpversion minor
	make prepare-release

bump-version-major:
	bumpversion major
	make prepare-release
