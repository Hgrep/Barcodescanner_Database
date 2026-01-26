"""
database.py

Service to manage the SQLite database for books and loans.

Data Inputs:
- book (dict): A dictionary representing a book with keys:
    'barcode', 'isbn', 'title', 'author', 'publisher', 'summary', 'keywords'
- barcode (str): Barcode of a book for lookup.
- book_id (int): ID of the book in the database.
- borrower (str): Name of the borrower.
- title (str), loan_date (str): Used for returning a loan.

Data Outputs:
- insert_book: Returns 'inserted' if new book added, 'updated' if book count incremented.
- find_book_by_barcode: Returns tuple (id, title, count) or None.
- get_all_books: Returns list of tuples with book info: 
  (title, barcode, isbn, author, publisher, summary, keywords, count)
- loan_book: None (creates a loan and decrements count)
- get_all_loans: Returns list of tuples with loan info: 
  (title, borrower, loan_date)
- return_loan: Returns True if loan successfully returned, False otherwise.
"""

import sqlite3
from datetime import datetime
from config import DATABASE_PATH


class DatabaseService:
    """Service for managing books and loans in a SQLite database."""

    def __init__(self):
        """Initialize database connection and create schema if missing."""
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self._create_schema()

    def _create_schema(self):
        """Create tables for books and loans if they do not exist."""
        cur = self.conn.cursor()

        # Books table
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

        # Loans table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            borrower TEXT,
            loan_date TEXT,
            return_date TEXT,
            FOREIGN KEY(book_id) REFERENCES books(id)
        )
        """)

        self.conn.commit()

    # ---------------- BOOKS ----------------

    def insert_book(self, book):
        """
        Insert a new book or increment count if already exists.

        Args:
            book (dict): Book data with keys:
                'barcode', 'isbn', 'title', 'author', 'publisher', 'summary', 'keywords'

        Returns:
            str: 'inserted' if new book added, 'updated' if count incremented.
        """
        cur = self.conn.cursor()

        cur.execute("""
        SELECT id FROM books WHERE barcode=? AND isbn=?
        """, (book["barcode"], book["isbn"]))

        row = cur.fetchone()

        if row:
            cur.execute("""
            UPDATE books SET count = count + 1 WHERE id=?
            """, (row[0],))
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
        """
        Find a book by barcode.

        Args:
            barcode (str): Barcode to search.

        Returns:
            tuple or None: (id, title, count) if found, else None.
        """
        cur = self.conn.cursor()
        cur.execute("""
        SELECT id, title, count FROM books WHERE barcode=?
        """, (barcode,))
        return cur.fetchone()

    def get_all_books(self):
        """
        Retrieve all books from the library.

        Returns:
            list of tuples: Each tuple contains:
            (title, barcode, isbn, author, publisher, summary, keywords, count)
        """
        cur = self.conn.cursor()
        cur.execute("""
        SELECT title, barcode, isbn, author, publisher, summary, keywords, count
        FROM books ORDER BY title
        """)
        return cur.fetchall()

    # ---------------- LOANS ----------------

    def loan_book(self, book_id, borrower):
        """
        Loan a book to a borrower and decrement available count.

        Args:
            book_id (int): ID of the book to loan.
            borrower (str): Name of the borrower.
        """
        cur = self.conn.cursor()

        cur.execute("""
        INSERT INTO loans (book_id, borrower, loan_date)
        VALUES (?, ?, ?)
        """, (
            book_id,
            borrower,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        cur.execute("""
        UPDATE books SET count = count - 1 WHERE id=? AND count > 0
        """, (book_id,))

        self.conn.commit()

    def get_all_loans(self):
        """
        Retrieve all current loans.

        Returns:
            list of tuples: Each tuple contains (title, borrower, loan_date)
        """
        cur = self.conn.cursor()
        cur.execute("""
        SELECT b.title, l.borrower, l.loan_date
        FROM loans l
        JOIN books b ON b.id = l.book_id
        ORDER BY l.loan_date DESC
        """)
        return cur.fetchall()

    # ---------------- RETURN LOAN ----------------

    def return_loan(self, title, borrower, loan_date):
        """
        Return a loaned book and increment its count.

        Args:
            title (str): Title of the loaned book.
            borrower (str): Borrower's name.
            loan_date (str): Date/time of the loan.

        Returns:
            bool: True if loan successfully returned, False if not found.
        """
        cur = self.conn.cursor()

        # Find the loaned book_id
        cur.execute("""
        SELECT b.id
        FROM books b
        JOIN loans l ON l.book_id = b.id
        WHERE b.title=? AND l.borrower=? AND l.loan_date=?
        """, (title, borrower, loan_date))
        row = cur.fetchone()
        if not row:
            return False  # Loan not found

        book_id = row[0]

        # Delete loan entry
        cur.execute("""
        DELETE FROM loans
        WHERE book_id=? AND borrower=? AND loan_date=?
        """, (book_id, borrower, loan_date))

        # Increment book count
        cur.execute("""
        UPDATE books SET count = count + 1 WHERE id=?
        """, (book_id,))

        self.conn.commit()
        return True
