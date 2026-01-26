"""
book_lookup.py

Service to fetch book metadata from OpenLibrary using ISBN.

Data Inputs:
- isbn (str): ISBN of the book to look up.

Data Outputs:
- dict with the following keys:
    - author (str): Author(s) of the book. Currently returned as empty string.
    - publisher (str): Publishers of the book (comma-separated if multiple).
    - summary (str): Description or summary of the book.
    - keywords (str): Keywords describing the book. Currently returned as empty string.
"""

import requests

class BookLookupService:
    """Service to fetch book metadata from OpenLibrary based on ISBN."""

    def lookup(self, isbn):
        """
        Look up a book on OpenLibrary by ISBN.

        Args:
            isbn (str): The ISBN number of the book.

        Returns:
            dict: Dictionary containing metadata keys:
                  'author', 'publisher', 'summary', 'keywords'.
                  Empty dict returned if lookup fails or ISBN not found.
        """
        url = f"https://openlibrary.org/isbn/{isbn}.json"

        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return {}

            data = r.json()

            return {
                "author": "",
                "publisher": ", ".join(data.get("publishers", [])),
                "summary": data.get("description", ""),
                "keywords": ""
            }

        except Exception:
            return {}
