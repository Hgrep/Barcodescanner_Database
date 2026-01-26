"""
isbn_lookup.py

Service to look up book metadata using ISBN or UPC codes via the EANSearch API.

Data Inputs:
- code (str): An ISBN-10, ISBN-13, or UPC barcode string.

Data Outputs:
- lookup(code): Returns a tuple (isbn, title)
    isbn (str | None): ISBN-10 of the book if found, else None
    title (str | None): Title of the book if found, else None
"""

from eansearch import EANSearch
from config import EANSEARCH_API_KEY

class ISBNLookupService:
    """
    Service for ISBN and UPC lookups using EANSearch API.
    Handles ISBN-10, ISBN-13, and UPC codes.
    """

    def __init__(self):
        """Initialize the EANSearch client using API key."""
        self.client = EANSearch(EANSEARCH_API_KEY)

    def lookup(self, code):
        """
        Lookup a book title and ISBN using a code (ISBN-10/13 or UPC).

        Args:
            code (str): ISBN-10, ISBN-13, or UPC barcode.

        Returns:
            tuple: (isbn, title)
                isbn (str | None): ISBN-10 if found, else None
                title (str | None): Book title if found, else None
        """
        print("LOOKUP INPUT:", repr(code))

        try:
            if len(code) == 13 and (code.startswith("978") or code.startswith("979")):
                isbn10 = self._isbn13_to_isbn10(code)
                print("ISBN13 → ISBN10:", isbn10)

                title = self.client.isbnLookup(isbn10)
                print("EANSEARCH TITLE:", repr(title))

                return isbn10, title

            if len(code) == 10:
                title = self.client.isbnLookup(code)
                print("EANSEARCH TITLE:", repr(title))
                return code, title

            # If not ISBN, treat as UPC
            product = self.client.barcodeSearch(code, 1)
            print("PRODUCT SEARCH RESULT:", repr(product))

            if not isinstance(product, dict):
                return None, None

            return product.get("isbn"), product.get("name")

        except Exception as e:
            print("LOOKUP EXCEPTION:", repr(e))
            return None, None

    def _isbn13_to_isbn10(self, isbn13):
        """
        Convert an ISBN-13 string to ISBN-10.

        Args:
            isbn13 (str): ISBN-13 string starting with 978 or 979.

        Returns:
            str: ISBN-10 string.
        """
        core = isbn13[3:-1]
        total = 0

        for i, digit in enumerate(core, 1):
            total += i * int(digit)

        checksum = total % 11
        checksum = "X" if checksum == 10 else str(checksum)

        return core + checksum
