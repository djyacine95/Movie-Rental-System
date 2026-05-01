import os
import sqlite3

DATABASE_PATH = os.environ.get("DATABASE_PATH", "movies.db")


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query_all(sql, params=()):
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return rows
    finally:
        conn.close()


def query_one(sql, params=()):
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return row
    finally:
        conn.close()


def execute(sql, params=()):
    conn = get_connection()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def create_tables():
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS Customers (
                CustomerID   INTEGER PRIMARY KEY AUTOINCREMENT,
                Name         TEXT    NOT NULL,
                Email        TEXT    NOT NULL UNIQUE,
                PhoneNumber  TEXT,
                Address      TEXT
            );

            CREATE TABLE IF NOT EXISTS Movies (
                MovieID      INTEGER PRIMARY KEY AUTOINCREMENT,
                Title        TEXT    NOT NULL,
                Genre        TEXT,
                ReleaseYear  INTEGER,
                Length       INTEGER,
                Rating       TEXT,
                Price        REAL    NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS Rentals (
                RentalID     INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerID   INTEGER NOT NULL,
                MovieID      INTEGER NOT NULL,
                RentalDate   TEXT    NOT NULL,
                ReturnDate   TEXT,
                FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
                FOREIGN KEY (MovieID)    REFERENCES Movies(MovieID)
            );

            CREATE TABLE IF NOT EXISTS Payments (
                PaymentID    INTEGER PRIMARY KEY AUTOINCREMENT,
                RentalID     INTEGER NOT NULL,
                Amount       REAL    NOT NULL,
                PaymentDate  TEXT    NOT NULL,
                FOREIGN KEY (RentalID) REFERENCES Rentals(RentalID)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()
