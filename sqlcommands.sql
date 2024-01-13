-- Templates for SQL queries and commands used in the making of this web app

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);

CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE IF NOT EXISTS "review" (
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    rating INTEGER,  -- changed column name here
    review TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

INSERT INTO review (
    user_id, 
    star_rating,
    review,
    date,
    time
)
VALUES (?);


SELECT title, author, star_rating FROM review WHERE user_id = (?)