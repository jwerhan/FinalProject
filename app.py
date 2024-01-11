import os

from datetime import datetime
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

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Logged in home page
@app.route("/", methods=["GET"])
@login_required
def index():
    """Logged in home page displays most recent additions to database for use (max of 4)"""

    reviews = db.execute("""SELECT title, author, star_rating, 
                         date FROM review WHERE user_id = ? 
                         ORDER BY date DESC, time DESC""", 
                         session["user_id"])
    
    count = db.execute("""SELECT COUNT(*) FROM review 
                       WHERE user_id = ?"""
                       , session["user_id"])
    
    length = count[0]["COUNT(*)"]
    if length > 4:
        length = 4
    star = "&#9733; "
    return render_template("index.html", reviews=reviews, length=int(length), star=star)
    

@app.route("/add-new", methods=["POST", "GET"])
@login_required
def addNew():
    """Add new entry to dataase"""
    if request.method == "POST":
        # Do things with the submitted data
        bookTitle = request.form.get("title")
        bookAuthor = request.form.get("author")
        bookRating = int(request.form.get("rating"))
        bookReview = request.form.get("review")
        if not bookTitle or not bookAuthor or not bookRating or not bookReview:
            return errorPage("Ensure all fields have valid information.")
        
        # Check if this user already has a review for this book
        count = db.execute("SELECT COUNT(*) FROM review WHERE user_id = ? AND title = ? AND author = ?", 
                           session["user_id"], bookTitle, bookAuthor)
        count = count[0]["COUNT(*)"] if count else 0
        if count != 0:
            return errorPage("""You have already reviewed this book, 
                             if you would like to update this review go to the update page""")

        # Get the current date and time
        currentDatetime = datetime.now()
        currentDate = currentDatetime.strftime("%Y-%m-%d")
        currentTime = currentDatetime.strftime("%H:%M:%S")

        db.execute("""INSERT INTO review (
                   user_id,
                   title,
                   author,
                   star_rating,
                   review,
                   date,
                   time
        ) VALUES (?)""", (session["user_id"], bookTitle, bookAuthor, bookRating, 
                          bookReview, currentDate, currentTime))

        return redirect("/")
    else:
        return render_template("add-new.html")


@app.route("/view-review", methods=["POST"])
@login_required
def viewReview():
    if request.method != "POST":
        return errorPage("Invalid Method", 405)
    title = request.form.get("review_title")
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    row = db.execute("""SELECT * FROM review
                        WHERE user_id = ?
                        AND title = ?""", 
                        session["user_id"], title)
    author = row[0]["author"]
    star_rating = row[0]["star_rating"]
    review = row[0]["review"]
    date = row[0]["date"]
    time = row[0]["time"]
    star = "&#9733; "
    username = users[0]["username"]

    return render_template("/view-review.html", title=title, author=author, star_rating=star_rating, 
                           review=review, star=star, username=username, date=date, time=time)

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return errorPage("Please enter a valid username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return errorPage("Please enter a valid password", 400)

        # Get username and password from form data
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username)
        
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return errorPage("Incorrect username or password", 403)
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/login.html")
    
# Registration route
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return errorPage("Please enter a valid username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return errorPage("Please enter a valid password", 400)

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return errorPage("please confirm password", 400)

        # Ensure password and confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return errorPage("Passwords do not match", 400)

        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        count = db.execute("SELECT COUNT(*) FROM users WHERE username = ?", username)

        # Ensure username does not already exist
        if int(count[0]["COUNT(*)"]) != 0:
            return errorPage("Username is already in use", 409)
        
        # Generate password hash
        hashkey = generate_password_hash(password, method="pbkdf2", salt_length=16)

        # Insert new user into database
        db.execute("INSERT INTO users (username, hash) VALUES (?)", (username, hashkey))

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return errorPage("invalid username and/or password", 400)

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        return render_template("/register.html")
    
    # Flash success message and redirect user to login page
    flash("Registration successful! Please log in.")
    return redirect("/login")