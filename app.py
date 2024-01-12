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
        length = int(length)
    star = "&#9733; "
    return render_template("index.html", reviews=reviews, length=length, star=star)
    

# Logged in search result page
@app.route("/search", methods=["GET"])
@login_required
def search():
    """Logged in search page displays search results for user"""
    if request.method == "GET":
        query = request.args.get("q")
        q=query
        if not query:
            return errorPage("Please enter a valid search query", 400)
        query = "%" + query + "%"
        
        # Pagination parameters
        page = request.args.get("page", default=1, type=int)
        results_per_page = 10
        offset = (page - 1) * results_per_page
        
        # Retrieve search results with pagination
        rows = db.execute("""SELECT review.title, review.author, review.rating, review.date, users.username 
                     FROM review 
                     JOIN users ON users.id = review.user_id
                     WHERE (review.title LIKE ? OR review.author LIKE ?) 
                     ORDER BY review.date DESC, review.time DESC
                     LIMIT ? OFFSET ?""", 
                     query, query, results_per_page, offset)
        
        # Count total number of search results
        count = db.execute("""SELECT COUNT(*) FROM review 
                           WHERE (title LIKE ? OR author LIKE ?)""", 
                            query, query)
        total_results = count[0]["COUNT(*)"]
        
        # Calculate total number of pages
        total_pages = ceil(total_results / results_per_page)
        
        star = "&#9733; "
        start = (page - 1) * results_per_page + 1  # Calculate the starting index of the current page
        end = min(start + results_per_page - 1, total_results)  # Calculate the ending index of the current page
        
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
@login_required
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
        star= "&#9733; "      
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

        return render_template("/update-review.html", title=title, author=author, 
                               rating=rating, review=review)

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