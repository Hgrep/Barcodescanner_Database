from keybert import KeyBERT

class KeywordExtractorService:
    def __init__(self):
        # Load once
        self.model = KeyBERT()

    def extract(self, text: str, max_keywords=8) -> str:
        """
        Extracts keywords from a text string (summary/blurb)
        Returns a comma-separated string of keywords
        """
        if not text or len(text.strip()) < 30:
            return ""

        # Generate keywords (1-2 word phrases)
        keywords = self.model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=max_keywords
        )

        # Return as comma-separated string
        return ", ".join(k for k, _ in keywords)
