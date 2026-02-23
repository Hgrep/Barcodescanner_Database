"""
main_window.py

Tkinter-based UI for the Book Barcode Scanner system.

Data Inputs:
- User scans barcodes via scanner or manual entry.
- User enters borrower names for loans.
- Search strings for filtering library or loans tables.

Data Outputs:
- Library tab: Displays all books with fields:
    Title, Barcode, ISBN, Author, Publisher, Keywords, Count
- Loans tab: Displays active loans with fields:
    Title, Borrower, Loan Date
- Log window: Shows scan, lookup, pipeline, and DB messages
- Dialogs: Ask user for confirmation or borrower names
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading

from services.scanner import ScannerService
from services.database import DatabaseService
from services.isbn_lookup import ISBNLookupService
from services.metadata_pipeline import MetadataPipeline
from services.card_printer import LibraryCardPrinter
from tkinter import filedialog


class MainWindow:
    """
    Main UI window for the barcode scanner system.
    Handles scanning, library display, loans, filtering, and returning books.
    """

    def __init__(self, root):
        """
        Initialize the UI components and services.

        Args:
            root (tk.Tk): The Tkinter root window.
        """
        
        self.root = root
        self.root.title("Book Barcode Scanner")

        # Services
        self.scanner = ScannerService()
        self.db = DatabaseService()
        self.isbn = ISBNLookupService()
        self.pipeline = MetadataPipeline()

        # Cached data for filtering
        self.library_cache = []
        self.loans_cache = []

        self.active_borrower = None

        self._build_ui()

    # -------------------- UI BUILDING --------------------

    def _build_ui(self):
        """Build the main notebook and tabs."""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.scan_tab = ttk.Frame(notebook)
        self.library_tab = ttk.Frame(notebook)
        self.loans_tab = ttk.Frame(notebook)
        self.cards_tab = ttk.Frame(notebook)

        notebook.add(self.scan_tab, text="Scanner")
        notebook.add(self.library_tab, text="Library")
        notebook.add(self.loans_tab, text="Loans")
        notebook.add(self.cards_tab, text="Library Cards")

        self._build_scan_tab()
        self._build_library_tab()
        self._build_loans_tab()
        self._build_cards_tab()

    # -------------------- SCANNER TAB --------------------

    def _build_scan_tab(self):
        """Create scan tab UI elements: entry, buttons, log window."""
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
        """Create library tab with search bar and treeview."""
        frame = ttk.Frame(self.library_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Search bar
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.library_search = ttk.Entry(search_frame)
        self.library_search.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.library_search.bind("<KeyRelease>", self.filter_library)

        # Treeview columns
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

        # --- Library card scan row ---
        card_frame = ttk.Frame(frame)
        card_frame.pack(fill=tk.X)

        ttk.Label(card_frame, text="Scan library card").pack(side=tk.LEFT)

        self.card_entry = ttk.Entry(card_frame)
        self.card_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.card_entry.bind("<Return>", self.on_card_scan)

        ttk.Button(
            card_frame,
            text="Clear Selection",
            command=self.clear_active_borrower
        ).pack(side=tk.RIGHT)

        self.borrower_label = ttk.Label(
            frame,
            text="No borrower selected",
            foreground="red"
        )
        self.borrower_label.pack(anchor="w", pady=(5, 10))

        # --- Book loan scan ---
        ttk.Label(frame, text="Scan book to loan out").pack(anchor="w")

        self.loan_entry = ttk.Entry(frame)
        self.loan_entry.pack(fill=tk.X, pady=5)
        self.loan_entry.bind("<Return>", self.on_loan_scan)

        # --- Search bar ---
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(5, 5))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.loan_search = ttk.Entry(search_frame)
        self.loan_search.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.loan_search.bind("<KeyRelease>", self.filter_loans)

        # --- Loans table ---
        cols = ("Title", "Borrower", "Loan Date")
        self.loan_tree = ttk.Treeview(frame, columns=cols, show="headings")

        for col in cols:
            self.loan_tree.heading(col, text=col)
            self.loan_tree.column(col, width=260, anchor="w")

        self.loan_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Button(frame, text="Refresh Loans", command=self.refresh_loans).pack()

        self.loan_tree.bind("<Double-1>", self.on_loan_return)
    
    def clear_active_borrower(self):
        self.active_borrower = None
        self.borrower_label.config(
        text="No borrower selected",
        foreground="red"
        )
        self.refresh_loans()
    # -------------------- SORTING --------------------

    def sort_by(self, col, descending):
        """
        Sort library treeview by column.

        Args:
            col (str): Column name
            descending (bool): Sort descending if True, ascending if False
        """
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
        """
        Log a message to the scan tab log window.

        Args:
            stage (str): Stage of processing (SCAN, LOOKUP, PIPELINE, DB)
            msg (str): Message to display
        """
        self.log.insert(tk.END, f"[{stage}] {msg}\n")
        self.log.see(tk.END)

    # -------------------- SCANNER METHODS --------------------

    def start_scan(self):
        """Start scanning and clear previous buffer."""
        self.scanner.start()
        self.scan_entry.focus_set()
        self.log_stage("STATE", "Scanning started")

    def stop_scan(self):
        """Stop scanning and process buffered barcodes asynchronously."""
        scans = self.scanner.stop()
        self.log_stage("STATE", f"Processing {len(scans)} barcodes...")
        threading.Thread(target=self.process_scans, args=(scans,), daemon=True).start()

    def on_scan(self, event):
        """
        Handle manual barcode entry via Return key.

        Args:
            event: Tkinter event
        """
        code = self.scan_entry.get().strip()
        self.scan_entry.delete(0, tk.END)
        self.scan_entry.focus_set()
        if not code:
            return
        self.scanner.add_scan(code)
        self.log_stage("SCAN", f"Scanned: {code}")

    def process_scans(self, scans):
        """
        Process scanned barcodes: lookup ISBN, enrich metadata, and insert into DB.

        Args:
            scans (list[str]): List of scanned barcode strings
        """
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

    # -------------------- LIBRARY METHODS --------------------

    def refresh_library(self):
        """Reload all books from DB and display in treeview."""
        self.tree.delete(*self.tree.get_children())
        self.library_cache = self.db.get_all_books()

        for row in self.library_cache:
            self.tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3], row[4], row[6], row[7]))

    def filter_library(self, event=None):
        """
        Filter library treeview based on search entry.

        Args:
            event: Tkinter event (optional)
        """
        query = self.library_search.get().lower().strip()
        self.tree.delete(*self.tree.get_children())
        for row in self.library_cache:
            text = " ".join(str(x).lower() for x in row)
            if query in text:
                self.tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3], row[4], row[6], row[7]))

    # -------------------- LOAN METHODS --------------------

    def on_loan_scan(self, event):
        """
        Handle scanning or entry of book to loan out.

        Args:
            event: Tkinter event
        """
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

        if not self.active_borrower:
            messagebox.showwarning(
                "No Borrower",
                "Please scan a library card first."
            )
            return

        borrower = self.active_borrower
        if not borrower:
            return

        self.db.loan_book(book_id, borrower)
        messagebox.showinfo("Loan Recorded", f"{title}\n\nLoaned to: {borrower}")

        self.refresh_library()
        self.refresh_loans()

    def refresh_loans(self):
        self.loan_tree.delete(*self.loan_tree.get_children())

        all_loans = self.db.get_all_loans()

        if self.active_borrower:
            self.loans_cache = [
                row for row in all_loans
                if row[1] == self.active_borrower
            ]
        else:
            self.loans_cache = all_loans

        for row in self.loans_cache:
            self.loan_tree.insert("", tk.END, values=row)
    def filter_loans(self, event=None):
        """
        Filter loans treeview based on search entry.

        Args:
            event: Tkinter event (optional)
        """
        query = self.loan_search.get().lower().strip()
        self.loan_tree.delete(*self.loan_tree.get_children())
        for row in self.loans_cache:
            text = " ".join(str(x).lower() for x in row)
            if query in text:
                self.loan_tree.insert("", tk.END, values=row)

    def on_loan_return(self, event):
        """
        Handle returning a loaned book when double-clicking a loan entry.

        Args:
            event: Tkinter double-click event
        """
        selected = self.loan_tree.selection()
        if not selected:
            return

        item = self.loan_tree.item(selected[0])
        title, borrower, loan_date = item["values"]

        if not messagebox.askyesno("Return Book", f"Return book?\n\n{title}"):
            return

        success = self.db.return_loan(title, borrower, loan_date)
        if success:
            messagebox.showinfo("Returned", f"{title} returned from {borrower}")
            self.refresh_library()
            self.refresh_loans()
        else:
            messagebox.showerror("Error", "Could not find this loan entry")

    # -------------------- LIBRARY CARDS TAB --------------------

    def _build_cards_tab(self):
        """Create Library Cards tab for managing accounts."""
        frame = ttk.Frame(self.cards_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Input section
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            input_frame,
            text="Enter account names (one per line):"
        ).pack(anchor="w")

        self.account_text = tk.Text(input_frame, height=6)
        self.account_text.pack(fill=tk.X, pady=5)

        ttk.Button(
            input_frame,
            text="Create Accounts",
            command=self.create_accounts
        ).pack(anchor="e")

        # Accounts list
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "Name")
        self.accounts_tree = ttk.Treeview(
            list_frame,
            columns=cols,
            show="headings",
            selectmode="extended"
        )

        self.accounts_tree.heading("ID", text="ID")
        self.accounts_tree.heading("Name", text="Name")
        self.accounts_tree.column("ID", width=80, anchor="center")
        self.accounts_tree.column("Name", width=300, anchor="w")

        self.accounts_tree.pack(fill=tk.BOTH, expand=True)

        # Buttons
        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, pady=6)

        ttk.Button(
            controls,
            text="Refresh Accounts",
            command=self.refresh_accounts
        ).pack(side=tk.LEFT)

        ttk.Button(
            controls,
            text="Print Cards",
            command=self.print_library_cards
        ).pack(side=tk.RIGHT)

    def create_accounts(self):
        """Create library accounts from text input."""
        raw = self.account_text.get("1.0", tk.END)
        names = [n.strip() for n in raw.splitlines() if n.strip()]

        if not names:
            messagebox.showwarning(
                "No Input",
                "Please enter at least one account name."
            )
            return

        created = 0
        for name in names:
            self.db.create_account(name)
            created += 1

        self.account_text.delete("1.0", tk.END)
        self.refresh_accounts()

        messagebox.showinfo(
            "Accounts Created",
            f"{created} account(s) processed."
        )

    def refresh_accounts(self):
        """Reload accounts from DB into treeview."""
        self.accounts_tree.delete(*self.accounts_tree.get_children())

        for account_id, name in self.db.get_all_accounts():
            self.accounts_tree.insert(
                "",
                tk.END,
                values=(account_id, name)
            )
    
    def print_library_cards(self):
        """
        Generate a double-sided A4 PDF of Code 128 library cards.
        Uses selected accounts; if none selected, prints all.
        """
        selected = self.accounts_tree.selection()

        if selected:
            names = [
                self.accounts_tree.item(item)["values"][1]
                for item in selected
            ]
        else:
            names = [name for _, name in self.db.get_all_accounts()]

        if not names:
            messagebox.showwarning(
                "No Accounts",
                "No accounts available to print."
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Library Cards PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )

        if not output_path:
            return

        try:
            printer = LibraryCardPrinter(output_path)
            printer.generate_pdf(names)

            messagebox.showinfo(
                "Cards Generated",
                f"Library cards created:\n\n{output_path}"
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to generate cards:\n\n{e}"
            )

    def on_card_scan(self, event):
        name = self.card_entry.get().strip()
        self.card_entry.delete(0, tk.END)

        if not name:
            return

        # Optional validation against accounts table
        if self.db.get_account_by_name(name) is None:
            if not messagebox.askyesno(
                "Unknown Borrower",
                f"'{name}' is not in accounts.\n\nUse anyway?"
            ):
                return

        self.active_borrower = name
        self.borrower_label.config(
            text=f"Borrower: {name}",
            foreground="green"
        )

        self.refresh_loans()