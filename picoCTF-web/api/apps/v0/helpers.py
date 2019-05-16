"""Helper functions required for v0 endpoints."""

from datetime import datetime
from functools import wraps

from bson import json_util
from flask import request, session
from voluptuous import Length, Required, Schema

import api
from api import check

user_login_schema = Schema({
    Required('username'):
    check(("Usernames must be between 3 and 50 characters.",
           [str, Length(min=3, max=50)]),),
    Required('password'):
    check(("Passwords must be between 3 and 50 characters.",
           [str, Length(min=3, max=50)]))
})


def WebSuccess(message=None, data=None):
    """Legacy successful response wrapper."""
    return json_util.dumps({
            'status': 1,
            'message': message,
            'data': data
        })


def WebError(message=None, data=None):
    """Legacy failure response wrapper."""
    return json_util.dumps({
            'status': 0,
            'message': message,
            'data': data
        })


def require_login(f):
    """Wrap routing functions that require a user to be logged in."""
    @wraps(f)
    def wrapper(*args, **kwds):
        if not api.user.is_logged_in():
            return WebError("You must be logged in")
        return f(*args, **kwds)

    return wrapper


def check_csrf(f):
    """Wrap routing functions that require a CSRF token."""
    @wraps(f)
    @require_login
    def wrapper(*args, **kwds):
        if 'token' not in session:
            return WebError("CSRF token not in session")
        if 'token' not in request.form:
            return WebError("CSRF token not in form")
        if session['token'] != request.form['token']:
            return WebError("CSRF token is not correct")
        return f(*args, **kwds)
    return wrapper


def block_before_competition():
    """Wrap routing functions that are blocked prior to the competition."""
    def decorator(f):
        """Inner decorator."""
        @wraps(f)
        def wrapper(*args, **kwds):
            if datetime.utcnow().timestamp() > api.config.get_settings(
            )["start_time"].timestamp():
                return f(*args, **kwds)
            else:
                return WebError("The competition has not begun yet!")
        return wrapper
    return decorator


def block_after_competition():
    """Wrap routing functions that are blocked after the competition."""
    def decorator(f):
        """Inner decorator."""
        @wraps(f)
        def wrapper(*args, **kwds):
            if datetime.utcnow().timestamp() < api.config.get_settings(
            )["end_time"].timestamp():
                return f(*args, **kwds)
            else:
                return WebError("The competition is over!")
        return wrapper
    return decorator
