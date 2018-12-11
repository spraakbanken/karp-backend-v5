default: test

update:
	pipenv install --dev

dev-run:
	pipenv run python run.py 8081

test: update
	pipenv run py.test tests
