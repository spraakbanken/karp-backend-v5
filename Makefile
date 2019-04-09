default: test

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

venv/req-dev.installed: setup.py
	venv/bin/python -m pip install -e .[dev]
	touch $@

dev-run: install-dev
	venv/bin/python run.py

test: install-dev
	venv/bin/python -m pytest --cov=src --cov-report=term-missing tests
	# venv/bin/python -m pytest tests

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
