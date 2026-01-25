import tkinter as tk
from tkinter import ttk
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

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X)

        ttk.Button(controls, text="Start Scan", command=self.start_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Stop & Process", command=self.stop_scan).pack(side=tk.LEFT, padx=5)

        self.scan_entry = ttk.Entry(frame)
        self.scan_entry.pack(fill=tk.X, pady=5)
        self.scan_entry.focus()

        self.log = tk.Text(frame, height=10)
        self.log.pack(fill=tk.X)

        search_frame = ttk.LabelFrame(frame, text="Search")
        search_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(search_frame, text="Search", command=self.search).pack()

        self.results = tk.Text(search_frame)
        self.results.pack(fill=tk.BOTH, expand=True)

        # Bind ENTER only to scan input field
        self.scan_entry.bind("<Return>", self.on_scan)

    def log_stage(self, stage, msg):
        self.log.insert(tk.END, f"[{stage}] {msg}\n")
        self.log.see(tk.END)

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

            # Use pipeline to fill missing fields
            meta = self.pipeline.enrich(isbn, initial)
            self.log_stage("PIPELINE", f"metadata after all services: {meta!r}")

            # Only write to DB once after all enrichment
            book = {
                "barcode": barcode,
                "isbn": isbn,
                "title": meta.get("title"),
                "author": meta.get("author", ""),
                "publisher": meta.get("publisher", ""),
                "summary": meta.get("summary", ""),
                "keywords": meta.get("keywords", "")
            }

            self.log_stage("DB", f"Inserting final record: {book!r}")
            self.db.insert_book(book)
            self.log_stage("DB", f"Inserted: {book['title']}")

    def search(self):
        term = self.search_entry.get()
        rows = self.db.search(term)

        self.results.delete(1.0, tk.END)
        for row in rows:
            self.results.insert(tk.END, f"{row}\n")
