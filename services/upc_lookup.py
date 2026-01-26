"""
upc_lookup.py

Service to look up products (including books) using their UPC codes.

Data Inputs:
- upc (str): A 12-digit or 13-digit UPC code string.

Data Outputs:
- lookup(upc): Returns a dictionary with metadata for the product/book.

Returned dictionary keys:
- title (str): Product or book title
- author (str): Brand name (for books, can serve as publisher)
- publisher (str): Same as author/brand
- summary (str): Empty string (UPC does not provide summary)
- keywords (str): Product category from UPC database
"""

import requests

class UPCLookupService:
    """
    Service that retrieves metadata for a given UPC code using the UPCitemdb API.
    """

    BASE_URL = "https://api.upcitemdb.com/prod/trial/lookup"

    def lookup(self, upc):
        """
        Lookup a UPC code and return book/product metadata.

        Args:
            upc (str): The UPC code to search for.

        Returns:
            dict: Metadata dictionary containing:
                - 'title': product title (str)
                - 'author': brand name / publisher (str)
                - 'publisher': brand name / publisher (str)
                - 'summary': empty string (str)
                - 'keywords': category (str)
            Returns an empty dict if lookup fails or no results found.
        """
        upc = upc.strip()
        try:
            r = requests.get(self.BASE_URL, params={"upc": upc}, timeout=5)
            if r.status_code != 200:
                print(f"[UPC ERROR] Status {r.status_code} for UPC {upc}")
                return {}

            data = r.json()
            if data.get("code") != "OK" or not data.get("items"):
                print(f"[UPC ERROR] No items found for UPC {upc}")
                return {}

            item = data["items"][0]

            return {
                "title": item.get("title"),
                "author": item.get("brand"),  # For books, brand can serve as publisher
                "publisher": item.get("brand"),
                "summary": "",
                "keywords": item.get("category")
            }

        except Exception as e:
            print(f"[UPC EXCEPTION] {e} for UPC {upc}")
            return {}
