"""
database.py

Service to manage the SQLite database for books, loans, and library accounts.

Data Inputs:
- book (dict): Book metadata
- barcode (str): Book barcode
- book_id (int): Book ID
- borrower (str): Borrower name (legacy)
- account_id (int): Library account ID
- title, loan_date: Used for returning loans

Data Outputs:
- Book, loan, and account query results
"""

import sqlite3
from datetime import datetime
from config import DATABASE_PATH


class DatabaseService:
    """Service for managing books, loans, and library accounts."""

    def __init__(self):
        """Initialize database connection and create schema if missing."""
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self._create_schema()

    def _create_schema(self):
        """Create tables and columns if they do not exist."""
        cur = self.conn.cursor()

        # ---------------- BOOKS ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            isbn TEXT,
            title TEXT,
            author TEXT,
            publisher TEXT,
            summary TEXT,
            keywords TEXT,
            count INTEGER DEFAULT 1,
            UNIQUE(barcode, isbn)
        )
        """)

        # ---------------- ACCOUNTS ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)

        # ---------------- LOANS ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            borrower TEXT,
            account_id INTEGER,
            loan_date TEXT,
            return_date TEXT,
            FOREIGN KEY(book_id) REFERENCES books(id),
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        )
        """)

        self.conn.commit()

    # ===================== BOOKS =====================

    def insert_book(self, book):
        cur = self.conn.cursor()

        cur.execute(
            "SELECT id FROM books WHERE barcode=? AND isbn=?",
            (book["barcode"], book["isbn"])
        )
        row = cur.fetchone()

        if row:
            cur.execute(
                "UPDATE books SET count = count + 1 WHERE id=?",
                (row[0],)
            )
            self.conn.commit()
            return "updated"

        cur.execute("""
        INSERT INTO books
        (barcode, isbn, title, author, publisher, summary, keywords, count)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            book["barcode"],
            book["isbn"],
            book["title"],
            book["author"],
            book["publisher"],
            book["summary"],
            book["keywords"]
        ))

        self.conn.commit()
        return "inserted"

    def find_book_by_barcode(self, barcode):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, title, count FROM books WHERE barcode=?",
            (barcode,)
        )
        return cur.fetchone()

    def get_all_books(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT title, barcode, isbn, author, publisher, summary, keywords, count
        FROM books ORDER BY title
        """)
        return cur.fetchall()

    # ===================== ACCOUNTS =====================

    def create_account(self, name):
        """Create a library account if it does not already exist."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO accounts (name) VALUES (?)",
            (name.strip(),)
        )
        self.conn.commit()

    def get_account_by_name(self, name):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name FROM accounts WHERE name=?",
            (name.strip(),)
        )
        return cur.fetchone()

    def get_account_by_id(self, account_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name FROM accounts WHERE id=?",
            (account_id,)
        )
        return cur.fetchone()

    def get_all_accounts(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name FROM accounts ORDER BY name"
        )
        return cur.fetchall()

    # ===================== LOANS (LEGACY) =====================

    def loan_book(self, book_id, borrower):
        """Legacy borrower-based loan."""
        cur = self.conn.cursor()

        cur.execute("""
        INSERT INTO loans (book_id, borrower, loan_date)
        VALUES (?, ?, ?)
        """, (
            book_id,
            borrower,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        cur.execute(
            "UPDATE books SET count = count - 1 WHERE id=? AND count > 0",
            (book_id,)
        )

        self.conn.commit()

    def get_all_loans(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT b.title, l.borrower, l.loan_date
        FROM loans l
        JOIN books b ON b.id = l.book_id
        ORDER BY l.loan_date DESC
        """)
        return cur.fetchall()

    # ===================== LOANS (ACCOUNTS) =====================

    def loan_book_to_account(self, book_id, account_id):
        """Loan a book to a library account."""
        cur = self.conn.cursor()

        cur.execute("""
        INSERT INTO loans (book_id, account_id, loan_date)
        VALUES (?, ?, ?)
        """, (
            book_id,
            account_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        cur.execute(
            "UPDATE books SET count = count - 1 WHERE id=? AND count > 0",
            (book_id,)
        )

        self.conn.commit()

    def get_loans_for_account(self, account_id):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT b.title, l.loan_date
        FROM loans l
        JOIN books b ON b.id = l.book_id
        WHERE l.account_id=?
        ORDER BY l.loan_date DESC
        """, (account_id,))
        return cur.fetchall()

    # ===================== RETURN LOAN =====================

    def return_loan(self, title, borrower, loan_date):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT b.id
        FROM books b
        JOIN loans l ON l.book_id = b.id
        WHERE b.title=? AND l.borrower=? AND l.loan_date=?
        """, (title, borrower, loan_date))

        row = cur.fetchone()
        if not row:
            return False

        book_id = row[0]

        cur.execute("""
        DELETE FROM loans
        WHERE book_id=? AND borrower=? AND loan_date=?
        """, (book_id, borrower, loan_date))

        cur.execute(
            "UPDATE books SET count = count + 1 WHERE id=?",
            (book_id,)
        )

        self.conn.commit()
        return True