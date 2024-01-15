# The following imports are intentionally unused
import csv
import datetime
import pytz
import requests
import urllib
import uuid

from flask import redirect, render_template, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    This decorator function is used to wrap routes that require the user to be logged in.
    If the user is not logged in, they will be redirected to the login page.

    Parameters:
    - f: The function to be decorated

    Returns:
    - The decorated function

    Example usage:
    @login_required
    def my_route():
        # Code that requires the user to be logged in
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def setOriginalAuthorTitle(author, title):
    """Set the original author and title of a book"""
    session["originalAuthor"] = author
    session["originalTitle"] = title

def getOriginalAuthorTitle():
    """Get the original author and title of a book"""
    return session["originalAuthor"], session["originalTitle"]

def clearOriginalAuthorTitle():
    """Clear the original author and title of a book"""
    session.pop("originalAuthor", None)
    session.pop("originalTitle", None)

# error page
def errorPage(message, code=400):
    """Render message so as to inform user of an error"""
    return render_template("error.html", code=code, message=message)