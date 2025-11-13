"""
Spell Corrector - Suggest corrections for misspelled queries
Uses simple edit distance and frequency-based correction
"""

import re
from typing import List, Optional, Dict, Set, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class SpellCorrector:
    """
    Spell correction using edit distance and word frequency
    Based on Peter Norvig's algorithm
    """
    
    def __init__(self, vocabulary: Optional[Set[str]] = None):
        """
        Initialize spell corrector
        
        Args:
            vocabulary: Set of known words (will be built from queries if None)
        """
        self.word_counts = Counter()
        self.vocabulary = vocabulary or set()
        
        # Load common words if no vocabulary provided
        if not self.vocabulary:
            self._load_common_words()
    
    def _load_common_words(self):
        """Load common English words"""
        # Common words (you can extend this or load from file)
        common_words = """
        the be to of and a in that have it for not on with he as you do at
        this but his by from they we say her she or an will my one all would
        there their what so up out if about who get which go me when make can
        like time no just him know take people into year your good some could
        them see other than then now look only come its over think also back
        after use two how our work first well way even new want because any
        these give day most us python programming code computer software
        tutorial learn development web data science machine learning algorithm
        """
        
        self.vocabulary.update(common_words.lower().split())
        logger.info(f"Loaded {len(self.vocabulary)} common words")
    
    def train(self, text: str):
        """
        Train corrector on text corpus
        
        Args:
            text: Training text
        """
        words = re.findall(r'\w+', text.lower())
        self.word_counts.update(words)
        self.vocabulary.update(words)
    
    def train_from_queries(self, queries: List[str]):
        """
        Train from search queries
        
        Args:
            queries: List of search queries
        """
        for query in queries:
            self.train(query)
    
    def correct(self, word: str) -> str:
        """
        Get best correction for a word
        
        Args:
            word: Potentially misspelled word
            
        Returns:
            Corrected word (or original if no correction found)
        """
        word = word.lower()
        
        # If word is known, return as is
        if word in self.vocabulary:
            return word
        
        # Get candidates
        candidates = self._candidates(word)
        
        # Return most common candidate
        if candidates:
            return max(candidates, key=self._word_probability)
        
        return word
    
    def suggest(self, word: str, max_suggestions: int = 3) -> List[Tuple[str, float]]:
        """
        Get multiple suggestions with confidence scores
        
        Args:
            word: Potentially misspelled word
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of (suggestion, confidence) tuples
        """
        word = word.lower()
        
        # If word is known, no suggestions needed
        if word in self.vocabulary:
            return [(word, 1.0)]
        
        # Get candidates
        candidates = self._candidates(word)
        
        if not candidates:
            return []
        
        # Score candidates
        scored = [
            (candidate, self._word_probability(candidate))
            for candidate in candidates
        ]
        
        # Sort by probability and return top N
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:max_suggestions]
    
    def correct_query(self, query: str) -> Tuple[str, List[str]]:
        """
        Correct all words in a query
        
        Args:
            query: Query string
            
        Returns:
            (corrected_query, list_of_corrections)
        """
        words = re.findall(r'\w+', query.lower())
        corrections = []
        corrected_words = []
        
        for word in words:
            corrected = self.correct(word)
            corrected_words.append(corrected)
            
            if corrected != word:
                corrections.append(f"{word} → {corrected}")
        
        corrected_query = ' '.join(corrected_words)
        return corrected_query, corrections
    
    def should_suggest_correction(self, query: str, threshold: float = 0.5) -> bool:
        """
        Determine if spell correction should be suggested
        
        Args:
            query: Query string
            threshold: Minimum ratio of unknown words to suggest correction
            
        Returns:
            True if correction should be suggested
        """
        words = re.findall(r'\w+', query.lower())
        
        if not words:
            return False
        
        unknown_count = sum(1 for word in words if word not in self.vocabulary)
        unknown_ratio = unknown_count / len(words)
        
        return unknown_ratio >= threshold
    
    def _candidates(self, word: str) -> Set[str]:
        """
        Generate candidate corrections
        
        Args:
            word: Word to correct
            
        Returns:
            Set of candidate words
        """
        # Priority order: known words, edits at distance 1, edits at distance 2
        return (
            self._known([word]) or
            self._known(self._edits1(word)) or
            self._known(self._edits2(word)) or
            {word}
        )
    
    def _known(self, words: Set[str]) -> Set[str]:
        """Return subset of words that are in vocabulary"""
        return set(w for w in words if w in self.vocabulary)
    
    def _edits1(self, word: str) -> Set[str]:
        """
        Generate all words one edit away
        
        Edits: delete, transpose, replace, insert
        """
        letters = 'abcdefghijklmnopqrstuvwxyz'
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        
        return set(deletes + transposes + replaces + inserts)
    
    def _edits2(self, word: str) -> Set[str]:
        """Generate all words two edits away"""
        return set(e2 for e1 in self._edits1(word) for e2 in self._edits1(e1))
    
    def _word_probability(self, word: str) -> float:
        """
        Calculate probability of word
        
        Args:
            word: Word to score
            
        Returns:
            Probability score
        """
        total_words = sum(self.word_counts.values()) or 1
        return self.word_counts.get(word, 1) / total_words
    
    def get_statistics(self) -> Dict:
        """
        Get corrector statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            'vocabulary_size': len(self.vocabulary),
            'trained_words': sum(self.word_counts.values()),
            'unique_words': len(self.word_counts),
            'most_common': self.word_counts.most_common(10)
        }


# Example usage
if __name__ == "__main__":
    # Initialize corrector
    corrector = SpellCorrector()
    
    # Train on sample queries (in production, use real search logs)
    sample_queries = [
        "python programming tutorial",
        "machine learning algorithms",
        "web development course",
        "data science project",
        "javascript framework",
        "python pandas tutorial",
        "machine learning model",
        "web scraping python"
    ]
    
    corrector.train_from_queries(sample_queries)
    
    print("="*60)
    print("Spell Correction Examples")
    print("="*60)
    
    # Test corrections
    test_words = [
        "pythn",      # python
        "programing", # programming
        "tutrial",    # tutorial
        "machien",    # machine
        "lerning",    # learning
        "javascrpt",  # javascript
        "devlopment", # development
    ]
    
    print("\nSingle Word Corrections:")
    for word in test_words:
        corrected = corrector.correct(word)
        suggestions = corrector.suggest(word, max_suggestions=3)
        
        print(f"\n'{word}'")
        print(f"  Best: {corrected}")
        print(f"  Suggestions: {[s[0] for s in suggestions]}")
    
    # Test query correction
    print("\n" + "="*60)
    print("Query Corrections:")
    print("="*60)
    
    test_queries = [
        "pythn programing tutrial",
        "machien lerning algorthm",
        "web devlopment corse"
    ]
    
    for query in test_queries:
        corrected, corrections = corrector.correct_query(query)
        print(f"\nOriginal: {query}")
        print(f"Corrected: {corrected}")
        if corrections:
            print(f"Changes: {', '.join(corrections)}")
    
    # Statistics
    print("\n" + "="*60)
    print("Statistics:")
    print("="*60)
    print(corrector.get_statistics())