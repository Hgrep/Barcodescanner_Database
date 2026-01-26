"""
keyword_extractor.py

Service to extract keywords from book summaries or text using the KeyBERT model.

Data Inputs:
- text (str): The summary, description, or any textual content of the book.
- max_keywords (int, optional): Maximum number of keywords to extract (default=8).

Data Outputs:
- extract(text, max_keywords): Returns a comma-separated string of keywords extracted from the text.
  Returns an empty string if the input text is too short or empty.
"""

from keybert import KeyBERT

class KeywordExtractorService:
    """
    Service to extract meaningful keywords from book summaries.
    Uses KeyBERT transformer-based model to identify key phrases.
    """

    def __init__(self):
        """
        Initialize the KeywordExtractorService.
        Loads the KeyBERT model once for reuse.
        """
        self.model = KeyBERT()

    def extract(self, text: str, max_keywords=8) -> str:
        """
        Extract keywords from a text string.

        Args:
            text (str): Input text (e.g., book summary).
            max_keywords (int, optional): Maximum number of keywords to return. Defaults to 8.

        Returns:
            str: Comma-separated keywords extracted from the text.
                 Returns an empty string if the input text is empty or shorter than 30 characters.
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
