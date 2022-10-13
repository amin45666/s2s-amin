from functools import wraps
from flask import redirect, session, url_for, flash


def roles_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session["role"] not in allowed_roles or session["role"] == "none":
                flash('Access denied')
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
