import sqlite3
from datetime import datetime
from config import DATABASE_PATH


class DatabaseService:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self._create_schema()

    def _create_schema(self):
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
        cur = self.conn.cursor()
        cur.execute("""
        SELECT id, title, count FROM books WHERE barcode=?
        """, (barcode,))
        return cur.fetchone()

    def get_all_books(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT title, barcode, isbn, author, publisher, summary, keywords, count
        FROM books ORDER BY title
        """)
        return cur.fetchall()

    # ---------------- LOANS ----------------

    def loan_book(self, book_id, borrower):
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
        cur = self.conn.cursor()
        cur.execute("""
        SELECT b.title, l.borrower, l.loan_date
        FROM loans l
        JOIN books b ON b.id = l.book_id
        ORDER BY l.loan_date DESC
        """)
        return cur.fetchall()
