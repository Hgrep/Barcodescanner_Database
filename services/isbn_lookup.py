from eansearch import EANSearch
from config import EANSEARCH_API_KEY


class ISBNLookupService:
    def __init__(self):
        self.client = EANSearch(EANSEARCH_API_KEY)

    def lookup(self, code):
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
        Convert ISBN-13 → ISBN-10
        """
        core = isbn13[3:-1]
        total = 0

        for i, digit in enumerate(core, 1):
            total += i * int(digit)

        checksum = total % 11
        checksum = "X" if checksum == 10 else str(checksum)

        return core + checksum
