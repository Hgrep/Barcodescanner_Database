import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from config import DATABASE_PATH


class DatabaseEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Editor")

        self.conn = sqlite3.connect(DATABASE_PATH)
        self._build_ui()
        self.load_books()
        self.load_loans()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.books_tab = ttk.Frame(notebook)
        self.loans_tab = ttk.Frame(notebook)

        notebook.add(self.books_tab, text="Books")
        notebook.add(self.loans_tab, text="Loans")

        self._build_books_tab()
        self._build_loans_tab()

    # -------------------- BOOKS --------------------

    def _build_books_tab(self):
        frame = ttk.Frame(self.books_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "Title", "Barcode", "ISBN", "Author", "Publisher", "Count")

        self.books_tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            self.books_tree.heading(col, text=col)
            self.books_tree.column(col, width=140, anchor="w")

        self.books_tree.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, pady=6)

        ttk.Button(controls, text="Refresh", command=self.load_books).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Edit Count", command=self.edit_count).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Delete Entry", command=self.delete_book).pack(side=tk.LEFT, padx=5)

    def load_books(self):
        self.books_tree.delete(*self.books_tree.get_children())
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, title, barcode, isbn, author, publisher, count FROM books
            ORDER BY title
        """)
        for row in cur.fetchall():
            self.books_tree.insert("", tk.END, values=row)

    def edit_count(self):
        selected = self.books_tree.selection()
        if not selected:
            return

        item = self.books_tree.item(selected[0])
        book_id, title, *_ , count = item["values"]

        new_count = simpledialog.askinteger(
            "Set Count",
            f"{title}\n\nCurrent count: {count}\n\nNew count:",
            minvalue=0,
            maxvalue=999
        )

        if new_count is None:
            return

        cur = self.conn.cursor()
        cur.execute("UPDATE books SET count=? WHERE id=?", (new_count, book_id))
        self.conn.commit()

        self.load_books()

    def delete_book(self):
        selected = self.books_tree.selection()
        if not selected:
            return

        item = self.books_tree.item(selected[0])
        book_id, title, *_ = item["values"]

        if not messagebox.askyesno("Confirm Delete", f"Delete:\n\n{title}?"):
            return

        cur = self.conn.cursor()
        cur.execute("DELETE FROM loans WHERE book_id=?", (book_id,))
        cur.execute("DELETE FROM books WHERE id=?", (book_id,))
        self.conn.commit()

        self.load_books()
        self.load_loans()

    # -------------------- LOANS --------------------

    def _build_loans_tab(self):
        frame = ttk.Frame(self.loans_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "Title", "Borrower", "Loan Date")

        self.loans_tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            self.loans_tree.heading(col, text=col)
            self.loans_tree.column(col, width=200, anchor="w")

        self.loans_tree.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, pady=6)

        ttk.Button(controls, text="Refresh", command=self.load_loans).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Delete Loan", command=self.delete_loan).pack(side=tk.LEFT, padx=5)

    def load_loans(self):
        self.loans_tree.delete(*self.loans_tree.get_children())
        cur = self.conn.cursor()
        cur.execute("""
            SELECT l.id, b.title, l.borrower, l.loan_date
            FROM loans l
            JOIN books b ON b.id = l.book_id
            ORDER BY l.loan_date DESC
        """)
        for row in cur.fetchall():
            self.loans_tree.insert("", tk.END, values=row)

    def delete_loan(self):
        selected = self.loans_tree.selection()
        if not selected:
            return

        item = self.loans_tree.item(selected[0])
        loan_id, title, borrower, _ = item["values"]

        if not messagebox.askyesno("Confirm Delete", f"Delete loan:\n\n{title}\n→ {borrower}?"):
            return

        cur = self.conn.cursor()
        cur.execute("DELETE FROM loans WHERE id=?", (loan_id,))
        self.conn.commit()

        self.load_loans()


if __name__ == "__main__":
    root = tk.Tk()
    DatabaseEditor(root)
    root.mainloop()
