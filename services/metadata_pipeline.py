from services.openlibrary import OpenLibraryService
from services.google_books import GoogleBooksService
from services.upc_lookup import UPCLookupService  # New service

class MetadataPipeline:
    def __init__(self):
        self.services = [
            OpenLibraryService(),
            GoogleBooksService(),
            UPCLookupService(),  # Last fallback for UPC
        ]

    def enrich(self, code, initial):
        """
        Enrich metadata by trying all services in order.
        Only fills empty fields.
        """
        result = dict(initial)

        for service in self.services:
            try:
                data = service.lookup(code)
                if data:
                    result = self._merge(result, data)
            except Exception as e:
                print(f"[PIPELINE ERROR] {service.__class__.__name__} failed: {e}")

        return result

    def _merge(self, base, incoming):
        for k, v in incoming.items():
            if not base.get(k) and v:
                base[k] = v
        return base
