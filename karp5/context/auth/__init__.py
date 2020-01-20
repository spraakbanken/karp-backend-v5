

check_user = None
validate_user = None


def init(auth_name: str):
    if auth_name == "dummy":
        global check_user, validate_user

