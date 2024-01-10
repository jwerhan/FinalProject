import os 

import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from functions import login_required, errorPage

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///books.db")

# Logged in home page
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET"])
@login_required
def index():
    """Logged in home page"""
    

# Login page (main landing paige
@app.route("/login", methods=["GET", "POST"])
def login():
    """Login new users"""
    
    # Clear session
    session.clear()

    # If form login submitted
    if request.method == "POST":
        # Perform checks on form inputs (check for valid username and pasword)
        if not request.form.get("username"):
            return errorPage("Please enter a username", 400)
        if not request.form.get("password"):
            return errorPage("Please enter a valid password", 400)
        
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username)
        
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return errorPage("Incorrect username or password", 403)
        
        # Remember user
        session["user_id"] = rows[0]["id"]

        # Return logged in home page if passed checks
        return render_template("/")

    # If loading page for the first time
    else:
        return render_template("/login.html")
    
# Registration route
@app.route("/register", methods=["GET", "POST"])
def register():
    """Refister new user"""

    if request.method == "POST":
        # Check for valid input
        if not request.form.get("username"):
            return errorPage("Please enter a valid username", 400)
        if not request.form.get("password"):
            return errorPage("Please enter a valid password", 400)
        elif not request.form.get("confirmation"):
            return errorPage("please confirm password", 400)

        username = request.form.get("username")
        password = request.form.get("password")

        # Check to see if username is already in the database
        count = db.execute("SELECT COUNT(*) FROM users WHERE username = ?", username)
        if int(count[0]["COUNT(*)"]) != 0:
            return errorPage("Username is already in use", 400)
        
        hashkey = generate_password_hash(password, method="pbkdf2", salt_length=16)
        # add username and haskey to db
        db.execute("INSERT INTO users (username, hash) VALUES (?)", (username, hashkey))

        # Ensure username was added to database
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return errorPage("invalid username and/or password", 400)
    elif request.method == "GET":
        return render_template("/register.html")
    
    # Send new users to home so they can login
    return redirect("/")