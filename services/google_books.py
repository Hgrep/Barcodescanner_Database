"""
google_books.py

Service to fetch book metadata from Google Books API using ISBN.

Data Inputs:
- isbn (str): The ISBN code of the book to search for.

Data Outputs:
- lookup: Returns a dictionary with possible keys:
    'title' (str): Title of the book
    'author' (str): Comma-separated list of authors
    'publisher' (str): Publisher name
    'summary' (str): Book description or summary
    'keywords' (str): Comma-separated categories
  Returns an empty dictionary {} if book is not found or request fails.
"""

import requests

class GoogleBooksService:
    """Service to query the Google Books API for book metadata."""

    BASE = "https://www.googleapis.com/books/v1/volumes"

    def lookup(self, isbn):
        """
        Lookup a book by its ISBN using the Google Books API.

        Args:
            isbn (str): ISBN of the book.

        Returns:
            dict: Book metadata with keys:
                'title', 'author', 'publisher', 'summary', 'keywords'.
                Returns empty dict if not found or error occurs.
        """
        try:
            r = requests.get(self.BASE, params={"q": f"isbn:{isbn}"}, timeout=5)
            data = r.json()

            if "items" not in data:
                return {}

            info = data["items"][0]["volumeInfo"]

            return {
                "title": info.get("title"),
                "author": ", ".join(info.get("authors", [])),
                "publisher": info.get("publisher"),
                "summary": info.get("description"),
                "keywords": ", ".join(info.get("categories", []))
            }

        except Exception:
            return {}
