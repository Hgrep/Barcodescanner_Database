import requests

class GoogleBooksService:
    BASE = "https://www.googleapis.com/books/v1/volumes"

    def lookup(self, isbn):
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
