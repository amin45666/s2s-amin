import random
import string


def login_authentication(email, password):
    """
    simple hardcoded loging to avoid undesired eyes
    """

    # hardcoded login for quick check
    if email == "admin@gmail.com" and password == "kudoadmin2022#":
        response = {
            "status": "allowed",
            "role": "sender",
        }
        return response
    else:
        response = {
            "status": "user unkown",
            "role": "sender",
        }
        return response


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    this generates our session ID
    """
    return "".join(random.choice(chars) for _ in range(size))
