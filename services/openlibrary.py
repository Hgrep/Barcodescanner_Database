"""
openlibrary.py

Service to fetch book metadata from OpenLibrary using ISBN.

Data Inputs:
- isbn (str): ISBN-10 or ISBN-13 of the book to look up.

Data Outputs:
- lookup(isbn): Returns a dictionary with book metadata:
    "title" (str): Book title if available
    "publisher" (str): Comma-separated string of publishers
    "summary" (str): Description/blurb of the book
"""
import requests


class OpenLibraryService:
    """
    Service to fetch book metadata from OpenLibrary.org
    """

    BASE = "https://openlibrary.org"

    def lookup(self, isbn):
        """
        Look up a book by ISBN on OpenLibrary.

        Args:
            isbn (str): ISBN-10 or ISBN-13 of the book.

        Returns:
            dict: Book metadata with keys:
                "title" (str): Book title
                "publisher" (str): Comma-separated publishers
                "summary" (str): Book description or summary
            Returns empty dict if lookup fails or data not found.
        """
        url = f"{self.BASE}/isbn/{isbn}.json"

        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return {}

            data = r.json()

            return {
                "title": data.get("title"),
                "publisher": ", ".join(data.get("publishers", [])),
                "summary": (
                    data.get("description", {}).get("value")
                    if isinstance(data.get("description"), dict)
                    else data.get("description")
                )
            }
        except Exception:
            return {}
