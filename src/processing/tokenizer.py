"""
Enhanced Tokenizer with Stemming and Stop Words
Provides better text processing for search
"""

import re
import unicodedata
from typing import List, Set
import logging

# Try to import NLTK components
try:
    from nltk.stem import PorterStemmer
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available. Install with: pip install nltk")

logger = logging.getLogger(__name__)


class Tokenizer:
    """
    Enhanced tokenizer with stemming and stop word removal
    """
    
    # Default English stop words (if NLTK not available)
    DEFAULT_STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
        'had', 'what', 'when', 'where', 'who', 'which', 'why', 'how'
    }
    
    def __init__(self, 
                 use_stemming: bool = True, 
                 use_stop_words: bool = True,
                 min_word_length: int = 2,
                 max_word_length: int = 50):
        """
        Initialize tokenizer with NLP features
        
        Args:
            use_stemming: Enable Porter Stemmer
            use_stop_words: Remove common stop words
            min_word_length: Minimum word length to keep
            max_word_length: Maximum word length to keep
        """
        self.use_stemming = use_stemming
        self.use_stop_words = use_stop_words
        self.min_word_length = min_word_length
        self.max_word_length = max_word_length
        
        # Initialize stemmer if available and enabled
        self.stemmer = None
        if use_stemming and NLTK_AVAILABLE:
            try:
                self.stemmer = PorterStemmer()
                logger.info("Porter Stemmer initialized")
            except Exception as e:
                logger.warning(f"Could not initialize stemmer: {e}")
                self.use_stemming = False
        elif use_stemming:
            logger.warning("Stemming requested but NLTK not available")
            self.use_stemming = False
        
        # Load stop words
        self.stop_words: Set[str] = set()
        if use_stop_words:
            if NLTK_AVAILABLE:
                try:
                    self.stop_words = set(stopwords.words('english'))
                    logger.info(f"Loaded {len(self.stop_words)} stop words from NLTK")
                except Exception as e:
                    logger.warning(f"Could not load NLTK stop words: {e}")
                    self.stop_words = self.DEFAULT_STOP_WORDS
            else:
                self.stop_words = self.DEFAULT_STOP_WORDS
                logger.info(f"Using default stop words ({len(self.stop_words)} words)")
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text by handling unicode and special characters
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Normalize unicode characters (é -> e, ñ -> n, etc.)
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into processed tokens
        
        Process:
        1. Normalize text (lowercase, unicode)
        2. Split into words
        3. Remove stop words (optional)
        4. Apply stemming (optional)
        5. Filter by length
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of processed tokens
        """
        if not text:
            return []
        
        # Step 1: Normalize text
        text = self.normalize_text(text)
        
        # Step 2: Split into words (alphanumeric only)
        # Keep numbers and letters, split on everything else
        words = re.findall(r'\b[a-z0-9]+\b', text)
        
        # Step 3: Remove stop words
        if self.use_stop_words:
            words = [w for w in words if w not in self.stop_words]
        
        # Step 4: Apply stemming
        if self.use_stemming and self.stemmer:
            words = [self.stemmer.stem(w) for w in words]
        
        # Step 5: Filter by length
        words = [
            w for w in words 
            if self.min_word_length <= len(w) <= self.max_word_length
        ]
        
        return words
    
    def tokenize_preserve_original(self, text: str) -> List[tuple]:
        """
        Tokenize while preserving original forms
        Useful for highlighting in search results
        
        Args:
            text: Input text
            
        Returns:
            List of (original_word, processed_token) tuples
        """
        if not text:
            return []
        
        # Extract original words
        original_words = re.findall(r'\b[a-zA-Z0-9]+\b', text)
        
        # Process each word
        result = []
        for original in original_words:
            # Normalize
            normalized = self.normalize_text(original)
            
            # Skip stop words
            if self.use_stop_words and normalized in self.stop_words:
                continue
            
            # Apply stemming
            if self.use_stemming and self.stemmer:
                processed = self.stemmer.stem(normalized)
            else:
                processed = normalized
            
            # Filter by length
            if self.min_word_length <= len(processed) <= self.max_word_length:
                result.append((original, processed))
        
        return result
    
    def get_statistics(self) -> dict:
        """
        Get tokenizer statistics
        
        Returns:
            Dictionary with tokenizer configuration
        """
        return {
            'stemming_enabled': self.use_stemming,
            'stop_words_enabled': self.use_stop_words,
            'stop_words_count': len(self.stop_words),
            'min_word_length': self.min_word_length,
            'max_word_length': self.max_word_length,
            'nltk_available': NLTK_AVAILABLE
        }
    
    def add_stop_words(self, words: List[str]) -> None:
        """
        Add custom stop words
        
        Args:
            words: List of words to add to stop words
        """
        self.stop_words.update(w.lower() for w in words)
    
    def remove_stop_words(self, words: List[str]) -> None:
        """
        Remove words from stop words list
        
        Args:
            words: List of words to remove from stop words
        """
        self.stop_words.difference_update(w.lower() for w in words)
    
    def test_tokenization(self, text: str) -> dict:
        """
        Test tokenization with detailed output
        Useful for debugging and understanding the process
        
        Args:
            text: Text to tokenize
            
        Returns:
            Dictionary with step-by-step results
        """
        result = {
            'original': text,
            'normalized': self.normalize_text(text),
            'raw_tokens': re.findall(r'\b[a-z0-9]+\b', self.normalize_text(text))
        }
        
        # Show stop words filtered
        if self.use_stop_words:
            result['after_stop_words'] = [
                w for w in result['raw_tokens'] 
                if w not in self.stop_words
            ]
            result['removed_stop_words'] = [
                w for w in result['raw_tokens'] 
                if w in self.stop_words
            ]
        
        # Show stemming
        if self.use_stemming and self.stemmer:
            base_tokens = result.get('after_stop_words', result['raw_tokens'])
            result['after_stemming'] = [self.stemmer.stem(w) for w in base_tokens]
            result['stemming_changes'] = [
                f"{orig} → {self.stemmer.stem(orig)}"
                for orig in base_tokens
                if orig != self.stemmer.stem(orig)
            ]
        
        # Final tokens
        result['final_tokens'] = self.tokenize(text)
        result['token_count'] = len(result['final_tokens'])
        
        return result


def setup_nltk():
    """
    Download required NLTK data
    Run this once to set up NLTK
    """
    if not NLTK_AVAILABLE:
        print("NLTK not installed. Install with: pip install nltk")
        return False
    
    import nltk
    
    try:
        print("Downloading NLTK data...")
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
        print("✓ NLTK data downloaded successfully")
        return True
    except Exception as e:
        print(f"✗ Error downloading NLTK data: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    # Test tokenizer
    tokenizer = Tokenizer(use_stemming=True, use_stop_words=True)
    
    test_texts = [
        "The quick brown foxes are running through the forest",
        "Python programming is amazing and powerful",
        "Searching for information on the internet"
    ]
    
    print("Tokenizer Test Results:")
    print("=" * 60)
    
    for text in test_texts:
        result = tokenizer.test_tokenization(text)
        print(f"\nOriginal: {result['original']}")
        print(f"Final tokens: {result['final_tokens']}")
        if 'stemming_changes' in result:
            print(f"Stemming changes: {result['stemming_changes']}")
        print("-" * 60)