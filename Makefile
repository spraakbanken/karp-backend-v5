dev-run:
	python dummyauth/wsauth.py
	pipenv run python run.py

test:
	pipenv run py.test tests
