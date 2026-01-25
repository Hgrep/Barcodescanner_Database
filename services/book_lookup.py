import requests

class BookLookupService:
    def lookup(self, isbn):
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
