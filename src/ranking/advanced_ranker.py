"""
Advanced Ranker - Phase 4
Integrates boolean operators, phrase search, wildcards, and filters
"""

from typing import List, Tuple, Dict, Optional
import re
from src.ranking.ranker import Ranker
from src.processing.query_parser import QueryParser, ParsedQuery
from src.processing.filter_processor import FilterProcessor
import logging

logger = logging.getLogger(__name__)


class AdvancedRanker(Ranker):
    """
    Advanced ranker with Phase 4 features:
    - Boolean operators (AND, OR, NOT)
    - Phrase search
    - Wildcard search
    - Advanced filters
    """
    
    def __init__(self, indexer, k1: float = 1.5, b: float = 0.75):
        """
        Initialize advanced ranker
        
        Args:
            indexer: Indexer instance
            k1: BM25 k1 parameter
            b: BM25 b parameter
        """
        super().__init__(indexer, k1, b)
        self.query_parser = QueryParser(indexer.tokenizer)
        self.filter_processor = FilterProcessor()
    
    def rank(self, 
             query: str, 
             top_k: int = 10,
             apply_filters: bool = True) -> List[Tuple[str, float]]:
        """
        Rank documents with advanced query features
        
        Args:
            query: Search query (may include operators and filters)
            top_k: Number of results to return
            apply_filters: Whether to apply filters
            
        Returns:
            List of (doc_id, score) tuples
        """
        # Parse query
        parsed = self.query_parser.parse(query)
        
        logger.info(f"Parsed query: {self.query_parser.explain_query(parsed)}")
        
        # Handle different query types
        if parsed.is_simple:
            # Simple query - use base ranker
            return super().rank(query, top_k)
        else:
            # Advanced query - use boolean/phrase matching
            return self._rank_advanced(parsed, top_k, apply_filters)
    
    def _rank_advanced(self, 
                      parsed: ParsedQuery, 
                      top_k: int,
                      apply_filters: bool) -> List[Tuple[str, float]]:
        """
        Rank with advanced features
        
        Args:
            parsed: Parsed query
            top_k: Number of results
            apply_filters: Apply filters
            
        Returns:
            Ranked results
        """
        # Get all candidate documents
        candidates = self._get_candidate_documents(parsed)
        
        if not candidates:
            return []
        
        # Score each candidate
        scored_results = []
        
        for doc_id in candidates:
            score = self._score_document(doc_id, parsed)
            
            if score > 0:
                scored_results.append((doc_id, score))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply filters if requested
        if apply_filters and parsed.filters:
            scored_results = self._apply_filters_to_results(
                scored_results, 
                parsed.filters
            )
        
        return scored_results[:top_k]
    
    def _get_candidate_documents(self, parsed: ParsedQuery) -> set:
        """Get candidate documents that might match the query"""
        candidates = set()
        
        # Start with documents containing any query term
        all_terms = (
            parsed.terms + 
            parsed.must_have + 
            parsed.should_have
        )
        
        for term in all_terms:
            if term in self.indexer.index:
                candidates.update(self.indexer.index[term].keys())
        
        # For phrase search, also get documents with phrase terms
        for phrase in parsed.phrases:
            phrase_terms = self.indexer.tokenizer.tokenize(phrase)
            for term in phrase_terms:
                if term in self.indexer.inverted_index:
                    candidates.update(self.indexer.inverted_index[term].keys())
        
        # Remove documents with NOT terms
        for term in parsed.must_not_have:
            if term in self.indexer.index:
                docs_to_remove = set(self.indexer.index[term].keys())
                candidates -= docs_to_remove
        
        return candidates
    
    def _score_document(self, doc_id: str, parsed: ParsedQuery) -> float:
        """Calculate score for a document given parsed query"""
        score = 0.0
        
        # Check required terms (AND)
        if parsed.must_have:
            if not self._document_contains_all(doc_id, parsed.must_have):
                return 0.0  # Document must contain all required terms
            
            # Add bonus for required terms
            for term in parsed.must_have:
                score += self._calculate_bm25_score(term, doc_id, 1) * 1.5
        
        # Check excluded terms (NOT)
        if parsed.must_not_have:
            if self._document_contains_any(doc_id, parsed.must_not_have):
                return 0.0  # Document must not contain excluded terms
        
        # Score regular terms
        for term in parsed.terms:
            term_score = self._calculate_bm25_score(term, doc_id, 1)
            score += term_score
        
        # Score phrases (exact match gets high bonus)
        for phrase in parsed.phrases:
            if self._document_contains_phrase(doc_id, phrase):
                score += 10.0  # High bonus for phrase match
        
        # Score OR terms (at least one should match)
        if parsed.should_have:
            or_score = max(
                (self._calculate_bm25_score(term, doc_id, 1) 
                 for term in parsed.should_have),
                default=0
            )
            score += or_score
        
        # Score wildcards
        for wildcard in parsed.wildcards:
            matching_terms = self._match_wildcard(wildcard)
            for term in matching_terms:
                if doc_id in self.indexer.inverted_index.get(term, {}):
                    score += self._calculate_bm25_score(term, doc_id, 1)
        
        return score
    
    def _document_contains_all(self, doc_id: str, terms: List[str]) -> bool:
        """Check if document contains all terms"""
        for term in terms:
            if term not in self.indexer.index:
                return False
            if doc_id not in self.indexer.index[term]:
                return False
        return True
    
    def _document_contains_any(self, doc_id: str, terms: List[str]) -> bool:
        """Check if document contains any term"""
        for term in terms:
            if term in self.indexer.index:
                if doc_id in self.indexer.index[term]:
                    return True
        return False
    
    def _document_contains_phrase(self, doc_id: str, phrase: str) -> bool:
        """
        Check if document contains exact phrase
        Note: This is simplified - proper implementation would check positions
        """
        phrase_terms = self.indexer.tokenizer.tokenize(phrase)
        
        # All terms must be in document
        for term in phrase_terms:
            if term not in self.indexer.inverted_index:
                return False
            if doc_id not in self.indexer.inverted_index[term]:
                return False
        
        # For now, just check all terms present
        # TODO: Check actual positions for exact phrase matching
        return True
    
    def _match_wildcard(self, wildcard: str) -> List[str]:
        """Match wildcard pattern against index terms"""
        # Convert wildcard to regex
        pattern = wildcard.replace('*', '.*')
        regex = re.compile(f'^{pattern}$')
        
        # Find matching terms in index
        matching = [
            term for term in self.indexer.index.keys()
            if regex.match(term)
        ]
        
        return matching
    
    def _apply_filters_to_results(self, 
                                  results: List[Tuple[str, float]], 
                                  filters: Dict[str, str]) -> List[Tuple[str, float]]:
        """Apply filters to scored results"""
        # This requires document metadata
        # For now, return as-is (filters should be applied at retrieval level)
        return results


# Example usage
if __name__ == "__main__":
    from src.processing.tokenizer import Tokenizer
    from src.storage.database import Database
    from src.indexing.indexer import Indexer
    
    # Initialize components
    tokenizer = Tokenizer(use_stemming=True, use_stop_words=True)
    database = Database()
    indexer = Indexer(database, tokenizer)
    
    # Add test documents
    docs = {
        'doc1': "Python is a programming language for web development",
        'doc2': "Python programming tutorial for beginners",
        'doc3': "Advanced Python programming techniques",
        'doc4': "Java programming language basics",
        'doc5': "Python and Java comparison"
    }
    
    for doc_id, text in docs.items():
        tokens = tokenizer.tokenize(text)
        indexer.add_document(doc_id, tokens)
    
    # Create advanced ranker
    ranker = AdvancedRanker(indexer)
    
    print("="*60)
    print("Advanced Ranker Examples")
    print("="*60)
    
    # Test queries
    test_queries = [
        "python programming",
        "python AND tutorial",
        "python NOT java",
        "python OR java",
        '"python programming"',
        "+python -java",
        "python* programming"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = ranker.rank(query, top_k=3)
        
        for doc_id, score in results:
            print(f"  {doc_id}: {score:.4f} - {docs[doc_id][:50]}...")