import requests

class UPCLookupService:
    BASE_URL = "https://api.upcitemdb.com/prod/trial/lookup"

    def lookup(self, upc):
        """
        Lookup a UPC code.
        Returns a dict:
            {'title': ..., 'brand': ..., 'category': ...}
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
                "author": item.get("brand"),  # For books, brand can be publisher
                "publisher": item.get("brand"),
                "summary": "",
                "keywords": item.get("category")
            }

        except Exception as e:
            print(f"[UPC EXCEPTION] {e} for UPC {upc}")
            return {}
