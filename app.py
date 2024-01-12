"""
This file contains the implementation of a Flask web application for a book review website.
The application allows users to register, login, search for books, add new book reviews, update existing reviews,
view reviews, and delete reviews. It uses a SQLite database to store user information and book reviews.
"""

import os

from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functions import login_required, errorPage
from math import ceil
from flask import url_for


# Configure application
app = Flask(__name__)

# Configure session to use cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_SECURE"] = True  # Enable secure cookies
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Enable HttpOnly cookies
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Set SameSite attribute to Lax
# Set secret key
app.secret_key = os.urandom(24)
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

    if not session["user_id"]:
        return redirect("/login")

    reviews = db.execute("""SELECT review.*, users.username FROM review 
                         JOIN users ON users.id = review.user_id
                         WHERE review.user_id = ? 
                         ORDER BY review.date DESC, review.time DESC""", 
                         session["user_id"])
    
    count = db.execute("""SELECT COUNT(*) FROM review 
                       WHERE user_id = ?"""
                       , session["user_id"])
    
    length = count[0]["COUNT(*)"]
    if length > 4:
        length = 4
    star = "&#9733; "
    return render_template("index.html", reviews=reviews, length=length, star=star)
    

@app.route("/search", methods=["GET"])
def search():
    """Logged in search page displays search results for user"""
    if request.method == "GET":
        query = request.args.get("q")
        q = query
        if not query:
            return errorPage("Please enter a valid search query", 400)

        query = "%" + query + "%"

        searchdb = SQL("sqlite:///books.db")


        # Pagination parameters
        page = request.args.get("page", default=1, type=int)
        results_per_page = 10
        offset = (page - 1) * results_per_page
        star = "&#9733; "

        # Retrieve search results with pagination
        rows = searchdb.execute("""SELECT review.title, review.author, review.rating, review.date, review.time, users.username
                                FROM review 
                                JOIN users ON users.id = review.user_id
                                WHERE (TRIM(review.title) LIKE ? OR TRIM(review.author) LIKE ?) 
                                ORDER BY CASE
                                    WHEN TRIM(review.title) LIKE ? THEN 0
                                    WHEN TRIM(review.title) LIKE ? || '%' THEN 1
                                    WHEN TRIM(review.title) LIKE '%' || ? || '%' THEN 2
                                    ELSE 3
                                END, review.date DESC, review.time DESC
                                LIMIT ? OFFSET ?""", 
                                query, query, query, query, query, results_per_page, offset)

        # Count total number of search results
        count = searchdb.execute("""SELECT COUNT(*) FROM review 
                           WHERE (title LIKE ? OR author LIKE ?)""", 
                            query, query)
        total_results = count[0]["COUNT(*)"]

        # Calculate total number of pages
        total_pages = ceil(total_results / results_per_page)

        if total_results == 1:
            # If there's only one result, render the template with the single result
            return render_template("search.html", reviews=rows, total_pages=total_pages, query=q,
                                current_page=page, star=star, start=1, end=1)

        start = (page - 1) * results_per_page + 1  # Calculate the starting index of the current page
        end = min(start + results_per_page, total_results)  # Calculate the ending index of the current page

        if total_results == 0:
            return errorPage("No results found", 404)

        return render_template("search.html", reviews=rows, total_pages=total_pages, query=q,
                               current_page=page, star=star, start=start, end=end)
    
@app.route("/add-new", methods=["POST", "GET"])
@login_required
def addNew():
    """Add new entry to database"""
    if request.method == "POST":
        # Do things with the submitted data
        bookTitle = request.form.get("title")
        bookAuthor = request.form.get("author")
        bookRating = int(request.form.get("rating"))
        bookReview = request.form.get("review")
        if not bookTitle or not bookAuthor or not bookRating or not bookReview:
            return errorPage("Ensure all fields have valid information.")

        # Preserve newlines in the review
        bookReview = bookReview.replace('\r\n', '<br>').replace('\n', '<br>')

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
                   rating,
                   review,
                   date,
                   time
        ) VALUES (?)""", (session["user_id"], bookTitle, bookAuthor, bookRating, 
                          bookReview, currentDate, currentTime))

        return redirect("/")
    else:
        return render_template("add-new.html", preserve_newlines=True)


@app.route("/view-review", methods=["GET"])
def viewReview():
    if request.method != "GET":
        return errorPage("Invalid Method", 405)
    title = request.args.get("review_title")
    reviewAuthor = request.args.get("review_author")
    review = db.execute("SELECT * FROM review JOIN users ON review.user_id = users.id WHERE title = ?", title)
    star = "&#9733; "
    return render_template("/view-review.html", title=title, review=review, star=star, reviewAuthor=reviewAuthor)

@app.route("/update-review", methods=["POST", "GET"])
@login_required
def updateReview():
    if request.method == "POST":
        title = request.form.get('title')
        author = request.form.get('author')
        rating = request.form.get('rating')
        review = request.form.get('review')  
              
        count = db.execute("""SELECT COUNT(*) FROM review 
                           WHERE user_id = ? AND title = ? AND author = ?""",
                            session["user_id"], title, author)
        count = count[0]["COUNT(*)"] if count else 0
        if count == 0:
            return errorPage("Review not found", 400)
        if not title or not author or not rating or not review:
            return errorPage("Ensure all fields have valid information.")
        
        db.execute("""UPDATE review SET rating = ?, review = ?
                   WHERE user_id = ? AND title = ? AND author = ?""",
                     rating, review, session["user_id"], title, author)
        
        return redirect(url_for("viewReview", review_title=title, review_author=author))
    
    else:
        query = request.args.get("q")

        row = db.execute("""SELECT * FROM review 
                     WHERE user_id = ? AND title = ?""",
                  session["user_id"], query,)
        if not row:
            return errorPage("Review not found", 400)
        count = len(row)
        if count > 1:
            return errorPage("Multiple reviews found, please be more specific", 400)
        
        title = row[0]["title"]
        author = row[0]["author"]
        rating = row[0]["rating"]
        review = row[0]["review"]
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])

        return render_template("/update-review.html", title=title, author=author, 
                               rating=rating, review=review, username=username)

@app.route("/update-search", methods=["GET"])
@login_required
def updateSearch():
    return render_template("/update-search.html")

@app.route("/search-review", methods=["POST", "GET"])
@login_required
def searchReview():
    pass

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

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

    # Add a return statement here to return a valid response
    return redirect("/")  # Replace "/" with the desired redirect URL

@app.route("/delete-review", methods=["POST", "GET"])
@login_required
def deleteReview():
    if request.method == "POST":
        title = request.form.get("q")
        author = request.form.get("author")
        db.execute("DELETE * FROM review WHERE user_id = ? AND title = ? AND author = ?",
                   session["user_id"], title, author)
        return redirect("/")
    else:
        title = request.args.get("q")
        author = request.args.get("author")
        review = db.execute("SELECT review FROM review WHERE title = ? AND user_id = ? AND author = ?", title, session["user_id"], author)
        return render_template("/delete-review.html", title=title, review=review, author=author, id=session["user_id"])
    
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