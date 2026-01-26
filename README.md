# Book Barcode Scanner

A desktop application to manage a personal or small library using barcode scanning.  
Supports scanning books, enriching metadata from online sources, managing loans, and tracking availability.

---

## Features

- Scan barcodes manually or via a barcode scanner.
- Lookup metadata for books using:
  - OpenLibrary API
  - Google Books API
  - UPC lookup
- Automatic keyword extraction from book summaries.
- Manage library inventory with counts and details.
- Track loans, borrowers, and loan dates.
- Return books and automatically update availability.
- Search and filter library and loans.
- Logging of scanning, lookup, pipeline, and database actions.

---

## Architecture

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/10119edf-48e3-431e-910a-222ad6e91fca" />




| Service                 | Purpose                                 |
| ----------------------- | --------------------------------------- |
| ScannerService          | Handles scanning buffer and state       |
| DatabaseService         | Manages SQLite DB for books and loans   |
| ISBNLookupService       | Lookup ISBN/UPC and get book title      |
| MetadataPipeline        | Enriches metadata from multiple sources |
| OpenLibraryService      | Fetch metadata from OpenLibrary API     |
| GoogleBooksService      | Fetch metadata from Google Books API    |
| UPCLookupService        | Fetch product/book data via UPC lookup  |
| KeywordExtractorService | Extract keywords from book summaries    |

**Database Schema**

**Books Table**

id: integer primary key

barcode: text

isbn: text

title: text

author: text

publisher: text

summary: text

keywords: text

count: integer

**Loans Table**

id: integer primary key

book_id: foreign key to books

borrower: text

loan_date: text

return_date: text

**Notes**

Deleting books.db removes both book data and loan records.

Keyword extraction requires a summary of at least ~30 characters.

Metadata enrichment always generates keywords from the summary.
---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/book-barcode-scanner.git
cd book-barcode-scanner

pip install -r requirements.txt

python app.py

---


## Build .exe (Windows)
pip install pyinstaller
#run in root directory
pyinstaller --onefile --windowed --name "BookScanner" app.py
