import requests

class OpenLibraryService:
    BASE = "https://openlibrary.org"

    def lookup(self, isbn):
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
