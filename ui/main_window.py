import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading

from services.scanner import ScannerService
from services.database import DatabaseService
from services.isbn_lookup import ISBNLookupService
from services.metadata_pipeline import MetadataPipeline


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Barcode Scanner")

        self.scanner = ScannerService()
        self.db = DatabaseService()
        self.isbn = ISBNLookupService()
        self.pipeline = MetadataPipeline()

        self.library_cache = []
        self.loans_cache = []

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.scan_tab = ttk.Frame(notebook)
        self.library_tab = ttk.Frame(notebook)
        self.loans_tab = ttk.Frame(notebook)

        notebook.add(self.scan_tab, text="Scanner")
        notebook.add(self.library_tab, text="Library")
        notebook.add(self.loans_tab, text="Loans")

        self._build_scan_tab()
        self._build_library_tab()
        self._build_loans_tab()

    # -------------------- SCANNER TAB --------------------

    def _build_scan_tab(self):
        frame = ttk.Frame(self.scan_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X)

        ttk.Button(controls, text="Start Scan", command=self.start_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Stop & Process", command=self.stop_scan).pack(side=tk.LEFT, padx=5)

        self.scan_entry = ttk.Entry(frame)
        self.scan_entry.pack(fill=tk.X, pady=5)
        self.scan_entry.focus()

        self.log = tk.Text(frame, height=12)
        self.log.pack(fill=tk.BOTH, expand=True)

        self.scan_entry.bind("<Return>", self.on_scan)

    # -------------------- LIBRARY TAB --------------------

    def _build_library_tab(self):
        frame = ttk.Frame(self.library_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.library_search = ttk.Entry(search_frame)
        self.library_search.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.library_search.bind("<KeyRelease>", self.filter_library)

        self.cols = ("Title", "Barcode", "ISBN", "Author", "Publisher", "Keywords", "Count")

        self.tree = ttk.Treeview(frame, columns=self.cols, show="headings")

        widths = {
            "Title": 260,
            "Barcode": 130,
            "ISBN": 130,
            "Author": 180,
            "Publisher": 200,
            "Keywords": 160,
            "Count": 70
        }

        for col in self.cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by(c, False))
            self.tree.column(col, width=widths.get(col, 140), anchor="w")

        self.tree.pack(fill=tk.BOTH, expand=True)

        ttk.Button(frame, text="Refresh Library", command=self.refresh_library).pack(pady=6)

    # -------------------- LOANS TAB --------------------

    def _build_loans_tab(self):
        frame = ttk.Frame(self.loans_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Scan book to loan out").pack(anchor="w")

        self.loan_entry = ttk.Entry(frame)
        self.loan_entry.pack(fill=tk.X, pady=5)
        self.loan_entry.bind("<Return>", self.on_loan_scan)

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(5, 5))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.loan_search = ttk.Entry(search_frame)
        self.loan_search.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.loan_search.bind("<KeyRelease>", self.filter_loans)

        cols = ("Title", "Borrower", "Loan Date")

        self.loan_tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            self.loan_tree.heading(col, text=col)
            self.loan_tree.column(col, width=260, anchor="w")

        self.loan_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Button(frame, text="Refresh Loans", command=self.refresh_loans).pack()

    # -------------------- SORTING --------------------

    def sort_by(self, col, descending):
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]

        try:
            data.sort(key=lambda t: int(t[0]), reverse=descending)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=descending)

        for idx, (_, child) in enumerate(data):
            self.tree.move(child, "", idx)

        self.tree.heading(col, command=lambda: self.sort_by(col, not descending))

    # -------------------- LOGGING --------------------

    def log_stage(self, stage, msg):
        self.log.insert(tk.END, f"[{stage}] {msg}\n")
        self.log.see(tk.END)

    # -------------------- SCAN PIPELINE --------------------

    def start_scan(self):
        self.scanner.start()
        self.scan_entry.focus_set()
        self.log_stage("STATE", "Scanning started")

    def stop_scan(self):
        scans = self.scanner.stop()
        self.log_stage("STATE", f"Processing {len(scans)} barcodes...")
        threading.Thread(target=self.process_scans, args=(scans,), daemon=True).start()

    def on_scan(self, event):
        code = self.scan_entry.get().strip()
        self.scan_entry.delete(0, tk.END)
        self.scan_entry.focus_set()

        if not code:
            return

        self.scanner.add_scan(code)
        self.log_stage("SCAN", f"Scanned: {code}")

    def process_scans(self, scans):
        for barcode in scans:
            self.log_stage("SCAN", f"Raw barcode: {barcode!r}")

            isbn, title = self.isbn.lookup(barcode)
            self.log_stage("LOOKUP", f"isbn={isbn!r}, title={title!r}")

            if not isbn:
                self.log_stage("ERROR", f"Lookup failed: {barcode}")
                continue

            initial = {
                "title": title,
                "author": "",
                "publisher": "",
                "summary": "",
                "keywords": ""
            }

            meta = self.pipeline.enrich(isbn, initial)
            self.log_stage("PIPELINE", f"metadata: {meta!r}")

            book = {
                "barcode": barcode,
                "isbn": isbn,
                "title": meta.get("title"),
                "author": meta.get("author", ""),
                "publisher": meta.get("publisher", ""),
                "summary": meta.get("summary", ""),
                "keywords": meta.get("keywords", "")
            }

            result = self.db.insert_book(book)
            self.log_stage("DB", f"{result.upper()}: {book['title']}")

        self.root.after(0, self.refresh_library)

    # -------------------- LIBRARY --------------------

    def refresh_library(self):
        self.tree.delete(*self.tree.get_children())

        self.library_cache = self.db.get_all_books()

        for row in self.library_cache:
            self.tree.insert("", tk.END, values=(
                row[0], row[1], row[2], row[3], row[4], row[6], row[7]
            ))

    def filter_library(self, event=None):
        query = self.library_search.get().lower().strip()

        self.tree.delete(*self.tree.get_children())

        for row in self.library_cache:
            text = " ".join(str(x).lower() for x in row)

            if query in text:
                self.tree.insert("", tk.END, values=(
                    row[0], row[1], row[2], row[3], row[4], row[6], row[7]
                ))

    # -------------------- LOANS --------------------

    def on_loan_scan(self, event):
        code = self.loan_entry.get().strip()
        self.loan_entry.delete(0, tk.END)

        if not code:
            return

        book = self.db.find_book_by_barcode(code)

        if not book:
            messagebox.showerror("Not Found", "Book not found in library")
            return

        book_id, title, count = book

        if count <= 0:
            messagebox.showwarning("Unavailable", f"No available copies:\n\n{title}")
            return

        if not messagebox.askyesno("Confirm Loan", f"Loan out:\n\n{title}?"):
            return

        borrower = simpledialog.askstring("Borrower", "Enter borrower's name:")

        if not borrower:
            return

        self.db.loan_book(book_id, borrower)

        messagebox.showinfo("Loan Recorded", f"{title}\n\nLoaned to: {borrower}")

        self.refresh_library()
        self.refresh_loans()

    def refresh_loans(self):
        self.loan_tree.delete(*self.loan_tree.get_children())

        self.loans_cache = self.db.get_all_loans()

        for row in self.loans_cache:
            self.loan_tree.insert("", tk.END, values=row)

    def filter_loans(self, event=None):
        query = self.loan_search.get().lower().strip()

        self.loan_tree.delete(*self.loan_tree.get_children())

        for row in self.loans_cache:
            text = " ".join(str(x).lower() for x in row)

            if query in text:
                self.loan_tree.insert("", tk.END, values=row)
