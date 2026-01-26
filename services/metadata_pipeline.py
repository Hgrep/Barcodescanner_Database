from services.openlibrary import OpenLibraryService
from services.google_books import GoogleBooksService
from services.upc_lookup import UPCLookupService
from services.keyword_extractor import KeywordExtractorService


class MetadataPipeline:
    def __init__(self):
        self.services = [
            OpenLibraryService(),
            GoogleBooksService(),
            UPCLookupService()
        ]

        self.keyword_service = KeywordExtractorService()

    def enrich(self, code, initial):
        """
        Enrich metadata by trying all services in order.
        Only fills empty fields.
        Always generates keywords from summary.
        """
        result = dict(initial)

        # Merge all services
        for service in self.services:
            try:
                data = service.lookup(code)
                if data:
                    result = self._merge(result, data)
            except Exception as e:
                print(f"[PIPELINE ERROR] {service.__class__.__name__} failed: {e}")

        # Always run keyword extraction on summary, even if previous keywords exist
        if result.get("summary"):
            try:
                result["keywords"] = self.keyword_service.extract(result["summary"], max_keywords=8)
            except Exception as e:
                print(f"[KEYWORD EXTRACTION ERROR]: {e}")

        return result

    def _merge(self, base, incoming):
        """
        Merge two metadata dicts: only fill missing fields in base.
        """
        for k, v in incoming.items():
            if v and not base.get(k):
                base[k] = v
        return base
