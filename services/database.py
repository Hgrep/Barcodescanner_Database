import sqlite3
from config import DATABASE_PATH

class DatabaseService:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self._create_schema()

    def _create_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            isbn TEXT,
            title TEXT,
            author TEXT,
            publisher TEXT,
            summary TEXT,
            keywords TEXT
        )
        """)
        self.conn.commit()

    def insert_book(self, book):
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO books 
        (barcode, isbn, title, author, publisher, summary, keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?)
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

    def search(self, text):
        q = f"%{text}%"
        cur = self.conn.cursor()
        cur.execute("""
        SELECT barcode, isbn, title, author, publisher, summary, keywords
        FROM books
        WHERE title LIKE ? OR author LIKE ? OR summary LIKE ? OR keywords LIKE ?
        """, (q, q, q, q))
        return cur.fetchall()
