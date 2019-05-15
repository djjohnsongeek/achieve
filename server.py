from flask import session, request, redirect, render_template
from functools import wraps

def login_required(f):
    """
    decorates routes to require login
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function