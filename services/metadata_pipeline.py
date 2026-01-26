"""
metadata_pipeline.py

Service pipeline to enrich book metadata using multiple external sources
and generate keywords from the book summary.

Data Inputs:
- code (str): ISBN, UPC, or other identifier used to look up the book.
- initial (dict): Initial metadata dictionary with possible keys:
    "title", "author", "publisher", "summary", "keywords"

Data Outputs:
- enrich(code, initial): Returns a metadata dictionary with enriched fields:
    "title", "author", "publisher", "summary", "keywords"
  Keywords are always extracted from the summary using KeywordExtractorService.
"""

from services.openlibrary import OpenLibraryService
from services.google_books import GoogleBooksService
from services.upc_lookup import UPCLookupService
from services.keyword_extractor import KeywordExtractorService


class MetadataPipeline:
    """
    Pipeline to enrich book metadata from multiple services.
    Uses OpenLibrary, GoogleBooks, UPC lookup, and keyword extraction.
    """

    def __init__(self):
        """
        Initialize the MetadataPipeline.
        Loads all services and the keyword extractor once for reuse.
        """
        self.services = [
            OpenLibraryService(),
            GoogleBooksService(),
            UPCLookupService()
        ]

        self.keyword_service = KeywordExtractorService()

    def enrich(self, code, initial):
        """
        Enrich metadata by sequentially querying all configured services.
        Only fills missing fields and always generates keywords from the summary.

        Args:
            code (str): ISBN, UPC, or barcode to look up.
            initial (dict): Initial metadata with possible keys:
                            'title', 'author', 'publisher', 'summary', 'keywords'

        Returns:
            dict: Enriched metadata with keys:
                  'title', 'author', 'publisher', 'summary', 'keywords'
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

        # Always run keyword extraction on summary
        if result.get("summary"):
            try:
                result["keywords"] = self.keyword_service.extract(result["summary"], max_keywords=8)
            except Exception as e:
                print(f"[KEYWORD EXTRACTION ERROR]: {e}")

        return result

    def _merge(self, base, incoming):
        """
        Merge two metadata dictionaries.
        Only fills missing fields in the base dictionary.

        Args:
            base (dict): Base metadata dictionary to update.
            incoming (dict): New metadata fields to merge.

        Returns:
            dict: Updated base dictionary with missing fields filled.
        """
        for k, v in incoming.items():
            if v and not base.get(k):
                base[k] = v
        return base
